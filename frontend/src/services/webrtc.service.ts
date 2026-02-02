/**
 * WebRTC Service for real-time video streaming.
 * Handles peer connection, SDP exchange, and ICE candidates.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface WebRTCConfig {
    sessionId: string;
    onConnected?: () => void;
    onDisconnected?: () => void;
    onError?: (error: Error) => void;
}

export class WebRTCService {
    private peerConnection: RTCPeerConnection | null = null;
    private localStream: MediaStream | null = null;
    private config: WebRTCConfig;
    private isConnected = false;

    constructor(config: WebRTCConfig) {
        this.config = config;
    }

    /**
     * Start WebRTC connection with camera stream.
     */
    async connect(): Promise<MediaStream> {
        try {
            // Get local camera stream
            this.localStream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 640 },
                    height: { ideal: 480 },
                    frameRate: { ideal: 30 }
                },
                audio: false // Audio handled separately
            });

            // Create peer connection with STUN servers
            this.peerConnection = new RTCPeerConnection({
                iceServers: [
                    { urls: 'stun:stun.l.google.com:19302' },
                    { urls: 'stun:stun1.l.google.com:19302' }
                ]
            });

            // Add local tracks to connection
            this.localStream.getTracks().forEach(track => {
                this.peerConnection!.addTrack(track, this.localStream!);
            });

            // Handle ICE candidates
            this.peerConnection.onicecandidate = (event) => {
                if (event.candidate) {
                    this.sendIceCandidate(event.candidate);
                }
            };

            // Handle connection state changes
            this.peerConnection.onconnectionstatechange = () => {
                const state = this.peerConnection?.connectionState;
                console.log('[WebRTC] Connection state:', state);

                if (state === 'connected') {
                    this.isConnected = true;
                    this.config.onConnected?.();
                } else if (state === 'disconnected' || state === 'failed') {
                    this.isConnected = false;
                    this.config.onDisconnected?.();
                }
            };

            // Create and send offer
            const offer = await this.peerConnection.createOffer();
            await this.peerConnection.setLocalDescription(offer);

            // Send offer to server
            const answer = await this.sendOffer(offer);
            
            // Set remote description (server's answer)
            await this.peerConnection.setRemoteDescription(
                new RTCSessionDescription(answer)
            );

            console.log('[WebRTC] Connection established');
            return this.localStream;

        } catch (error) {
            console.error('[WebRTC] Connection failed:', error);
            this.config.onError?.(error as Error);
            throw error;
        }
    }

    /**
     * Send SDP offer to backend.
     */
    private async sendOffer(offer: RTCSessionDescriptionInit): Promise<RTCSessionDescriptionInit> {
        const response = await fetch(`${API_BASE}/video/webrtc/offer`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                sdp: offer.sdp,
                type: offer.type,
                session_id: this.config.sessionId
            })
        });

        if (!response.ok) {
            throw new Error(`SDP exchange failed: ${response.statusText}`);
        }

        return response.json();
    }

    /**
     * Send ICE candidate to backend.
     */
    private async sendIceCandidate(candidate: RTCIceCandidate): Promise<void> {
        try {
            await fetch(`${API_BASE}/video/webrtc/ice`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    candidate: candidate.candidate,
                    sdpMid: candidate.sdpMid,
                    sdpMLineIndex: candidate.sdpMLineIndex,
                    session_id: this.config.sessionId
                })
            });
        } catch (error) {
            console.warn('[WebRTC] Failed to send ICE candidate:', error);
        }
    }

    /**
     * Get local video stream.
     */
    getLocalStream(): MediaStream | null {
        return this.localStream;
    }

    /**
     * Check if connected.
     */
    isActive(): boolean {
        return this.isConnected;
    }

    /**
     * Disconnect and cleanup.
     */
    async disconnect(): Promise<void> {
        // Close connection on server
        try {
            await fetch(`${API_BASE}/video/webrtc/close?session_id=${this.config.sessionId}`, {
                method: 'POST'
            });
        } catch (error) {
            console.warn('[WebRTC] Failed to close server connection:', error);
        }

        // Stop local tracks
        this.localStream?.getTracks().forEach(track => track.stop());
        this.localStream = null;

        // Close peer connection
        this.peerConnection?.close();
        this.peerConnection = null;

        this.isConnected = false;
        console.log('[WebRTC] Disconnected');
    }
}

// Factory function for easy use
export function createWebRTCService(config: WebRTCConfig): WebRTCService {
    return new WebRTCService(config);
}
