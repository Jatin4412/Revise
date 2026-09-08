/**
 * UI-side boundary for communicating with the Reiterate engine.
 *
 * Keep transport details here so React components do not depend on engine
 * implementation details. The HTTP adapter can be replaced later without
 * changing the chat UI.
 */

export type EngineMode = "auto" | "lite" | "basic" | "pro";

export interface EngineModel {
  provider: string;
  model?: string;
}

export interface EngineRequest {
  prompt: string;
  mode?: EngineMode;
  primary_model?: EngineModel;
  secondary_model?: EngineModel;
}

export interface EngineResponse {
  text: string;
  decision: "accept" | "revise" | "ask";
  version_id: string;
}

interface EngineErrorResponse {
  error?: {
    code?: string;
    message?: string;
  };
}

export interface EngineClient {
  request(request: EngineRequest): Promise<EngineResponse>;
}

const ENGINE_BASE_URL = "http://127.0.0.1:8000";

export function createEngineClient(baseUrl = ENGINE_BASE_URL): EngineClient {
  return {
    async request(request) {
      let response: Response;

      try {
        response = await fetch(`${baseUrl}/v1/engine`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(request),
        });
      } catch {
        throw new Error("ENGINE_UNREACHABLE");
      }

      if (!response.ok) {
        let message = "ENGINE_ERROR";

        try {
          const body = (await response.json()) as EngineErrorResponse;
          message = body.error?.message || message;
        } catch {
          // Keep the UI-facing error generic when the response is not JSON.
        }

        throw new Error(message);
      }

      const result = (await response.json()) as EngineResponse;

      if (typeof result.text !== "string") {
        throw new Error("INVALID_ENGINE_RESPONSE");
      }

      return result;
    },
  };
}
