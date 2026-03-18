import client, { type ApiResponse, extractErrorResponse } from '../client';

export interface AnalysisSection {
  title: string;
  content: string;
}

export interface ChatFlowItem {
  point: string;
  내용: string;
}

export interface FileNode {
  name: string;
  path: string;
  type: 'file' | 'directory';
  children?: FileNode[];
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

export async function listFiles(
  path: string,
): Promise<ApiResponse<{ tree: FileNode }>> {
  try {
    const res = await client.get('/api/legacy/files', { params: { path } });
    return res.data;
  } catch (e) {
    return extractErrorResponse(e);
  }
}

export async function readFile(
  path: string,
): Promise<ApiResponse<{ path: string; content: string }>> {
  try {
    const res = await client.get('/api/legacy/file', { params: { path } });
    return res.data;
  } catch (e) {
    return extractErrorResponse(e);
  }
}

export async function sendChat(
  codePath: string,
  question: string,
  focusedFile?: string | null,
): Promise<ApiResponse<{ code_path: string; answer: string; flow: ChatFlowItem[] }>> {
  try {
    const res = await client.post('/api/legacy/chat', {
      code_path: codePath,
      question,
      focused_file: focusedFile ?? null,
    });
    return res.data;
  } catch (e) {
    return extractErrorResponse(e);
  }
}
