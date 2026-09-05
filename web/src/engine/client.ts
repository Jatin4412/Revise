/**
 * UI-side boundary for communicating with the Reiterate engine.
 *
 * Keep transport details here so React components do not depend on engine
 * implementation details. The concrete transport can be wired when the
 * engine's public interface is finalized.
 */
export interface EngineRequest {
  type: string;
  payload?: unknown;
}

export interface EngineResponse<T = unknown> {
  type: string;
  payload?: T;
  error?: string;
}

export interface EngineClient {
  request<T = unknown>(request: EngineRequest): Promise<EngineResponse<T>>;
}

export function createEngineClient(): EngineClient {
  return {
    async request() {
      throw new Error("Engine transport is not configured yet.");
    },
  };
}
