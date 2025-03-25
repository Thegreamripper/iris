import OpenAI from 'openai';

const openai = new OpenAI({
  apiKey: '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',
  dangerouslyAllowBrowser: true
});

export interface Message {
  role: 'user' | 'assistant';
  content: string;
}

// Store learned responses
const learnedResponses = new Map<string, string>();

// Function to find similar questions in history
const findSimilarQuestion = (question: string): string | null => {
  const similarityThreshold = 0.8;
  // Simple word matching for similarity
  return Array.from(learnedResponses.keys()).find(key => {
    const words1 = question.toLowerCase().split(' ');
    const words2 = key.toLowerCase().split(' ');
    const commonWords = words1.filter(word => words2.includes(word));
    return commonWords.length / Math.max(words1.length, words2.length) > similarityThreshold;
  }) || null;
};

// Function to learn from successful interactions
const learnFromInteraction = (question: string, response: string) => {
  learnedResponses.set(question, response);
  // Store only last 1000 learned responses to manage memory
  if (learnedResponses.size > 1000) {
    const keys = Array.from(learnedResponses.keys());
    if (keys.length > 0) {
      learnedResponses.delete(keys[0]);
    }
  }
};

export const generateResponse = async (messages: Message[]): Promise<string> => {
  try {
    const userMessage = messages[messages.length - 1].content;
    
    // Check if we have a learned response
    const similarQuestion = findSimilarQuestion(userMessage);
    if (similarQuestion) {
      const learnedResponse = learnedResponses.get(similarQuestion);
      if (learnedResponse) {
        return learnedResponse;
      }
    }

    // If no learned response, use OpenAI
    const completion = await openai.chat.completions.create({
      messages: messages.map(msg => ({
        role: msg.role,
        content: msg.content
      })),
      model: 'gpt-3.5-turbo',
      temperature: 0.7,
      max_tokens: 1000
    });

    const response = completion.choices[0]?.message?.content || 
      'I apologize, but I could not generate a response.';

    // Learn from this interaction
    learnFromInteraction(userMessage, response);
    
    return response;
  } catch (error) {
    console.error('Error generating response:', error);
    // Try to provide a fallback response from learned responses
    const fallbackResponse = Array.from(learnedResponses.values())[0];
    if (fallbackResponse) {
      return `I'm having trouble connecting, but based on what I've learned: ${fallbackResponse}`;
    }
    throw new Error('Failed to generate response');
  }
}; 