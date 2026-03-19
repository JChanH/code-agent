import client, { type ApiResponse, extractErrorResponse } from '../client';
import type { RuntimeErrorListResponse } from '../../types';

export async function getRuntimeErrors(params: { limit?: number; offset?: number } = {}): Promise<ApiResponse<RuntimeErrorListResponse>> {
  try {
    const res = await client.get<ApiResponse<RuntimeErrorListResponse>>('/api/runtime-errors', { params });
    return res.data;
  } catch (e) {
    return extractErrorResponse(e);
  }
}

export async function getRuntimeErrorsByProject(
  projectId: string,
  params: { limit?: number; offset?: number } = {},
): Promise<ApiResponse<RuntimeErrorListResponse>> {
  try {
    const res = await client.get<ApiResponse<RuntimeErrorListResponse>>(
      `/api/runtime-errors/project/${projectId}`,
      { params },
    );
    return res.data;
  } catch (e) {
    return extractErrorResponse(e);
  }
}
