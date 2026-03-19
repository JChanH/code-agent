import client, { type ApiResponse, extractErrorResponse } from '../client';
import type { RuntimeError, RuntimeErrorListResponse, RuntimeErrorStatus } from '../../types';

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

export async function updateRuntimeErrorStatus(
  errorId: string,
  status: RuntimeErrorStatus,
): Promise<ApiResponse<RuntimeError>> {
  try {
    const res = await client.patch<ApiResponse<RuntimeError>>(
      `/api/runtime-errors/${errorId}/status`,
      { status },
    );
    return res.data;
  } catch (e) {
    return extractErrorResponse(e);
  }
}

export async function updateRuntimeErrorSourcePath(
  errorId: string,
  sourcePath: string,
): Promise<ApiResponse<RuntimeError>> {
  try {
    const res = await client.patch<ApiResponse<RuntimeError>>(
      `/api/runtime-errors/${errorId}/source-path`,
      { source_path: sourcePath },
    );
    return res.data;
  } catch (e) {
    return extractErrorResponse(e);
  }
}
