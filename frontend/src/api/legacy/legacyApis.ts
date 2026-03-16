import client, { type ApiResponse, extractErrorResponse } from '../client';

export interface AnalysisSection {
  title: string;
  content: string;
}

export async function startAnalysis(
  sessionId: string,
  codePath: string,
): Promise<ApiResponse<{ session_id: string; status: string }>> {
  try {
    const res = await client.post('/api/legacy/analyze', {
      session_id: sessionId,
      code_path: codePath,
    });
    return res.data;
  } catch (e) {
    return extractErrorResponse(e);
  }
}

export async function sendChat(
  sessionId: string,
  question: string,
): Promise<ApiResponse<{ session_id: string; answer: string }>> {
  try {
    const res = await client.post('/api/legacy/chat', {
      session_id: sessionId,
      question,
    });
    return res.data;
  } catch (e) {
    return extractErrorResponse(e);
  }
}
