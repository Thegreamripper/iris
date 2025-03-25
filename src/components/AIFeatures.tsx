import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';

interface AIResponse {
  transcription?: string;
  emotion?: string;
  speaker_id?: number[];
  is_speech?: boolean;
}

const AIFeatures: React.FC = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [response, setResponse] = useState('');
  const [emotion, setEmotion] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  useEffect(() => {
    // Request microphone permissions
    navigator.mediaDevices.getUserMedia({ audio: true })
      .then(stream => {
        mediaRecorderRef.current = new MediaRecorder(stream);
        
        mediaRecorderRef.current.ondataavailable = (event) => {
          audioChunksRef.current.push(event.data);
        };

        mediaRecorderRef.current.onstop = async () => {
          const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
          await processAudio(audioBlob);
          audioChunksRef.current = [];
        };
      })
      .catch(err => console.error('Error accessing microphone:', err));
  }, []);

  const startRecording = () => {
    if (mediaRecorderRef.current) {
      audioChunksRef.current = [];
      mediaRecorderRef.current.start();
      setIsRecording(true);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const processAudio = async (audioBlob: Blob) => {
    setIsProcessing(true);
    try {
      const formData = new FormData();
      formData.append('file', audioBlob);

      const response = await axios.post('http://localhost:8000/process-audio', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      const data: AIResponse = response.data;
      
      if (data.transcription) {
        setTranscript(data.transcription);
        // Generate AI response
        const aiResponse = await axios.post('http://localhost:8000/generate-response', {
          text: data.transcription
        });
        setResponse(aiResponse.data.response);
      }
      
      if (data.emotion) {
        setEmotion(data.emotion);
      }

      // Convert response to speech
      const ttsResponse = await axios.post('http://localhost:8000/text-to-speech', {
        text: response
      });

      // Play the audio response
      const audio = new Audio('data:audio/wav;base64,' + btoa(ttsResponse.data.audio));
      audio.play();

    } catch (error) {
      console.error('Error processing audio:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <div className="bg-white/10 p-6 rounded-lg backdrop-blur-lg">
        <h2 className="text-2xl font-bold mb-4">Voice Interaction</h2>
        
        <button
          onClick={isRecording ? stopRecording : startRecording}
          className={`px-6 py-3 rounded-lg ${
            isRecording 
              ? 'bg-red-500 hover:bg-red-600' 
              : 'bg-blue-500 hover:bg-blue-600'
          } text-white transition-colors`}
          disabled={isProcessing}
        >
          {isRecording ? 'Stop Recording' : 'Start Recording'}
        </button>

        {isProcessing && (
          <div className="mt-4">
            <div className="loading-dots">Processing</div>
          </div>
        )}

        {transcript && (
          <div className="mt-6 space-y-4">
            <div className="bg-white/5 p-4 rounded-lg">
              <h3 className="font-semibold mb-2">Transcript:</h3>
              <p>{transcript}</p>
            </div>

            {emotion && (
              <div className="bg-white/5 p-4 rounded-lg">
                <h3 className="font-semibold mb-2">Detected Emotion:</h3>
                <p>{emotion}</p>
              </div>
            )}

            {response && (
              <div className="bg-white/5 p-4 rounded-lg">
                <h3 className="font-semibold mb-2">AI Response:</h3>
                <p>{response}</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default AIFeatures; 