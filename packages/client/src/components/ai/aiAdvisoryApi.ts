import axios from "axios";

export interface AIContextPacket {
  schema_id: "ai_context_packet_v1";
  created_at_utc: string;
  request: Record<string, any>;
  evidence: Record<string, any>;
  excerpts?: Record<string, any>;
}

export async function requestAdvisory(packet: AIContextPacket) {
  const res = await axios.post("/ai/advisories/request", packet, {
    headers: { "X-Request-Id": crypto.randomUUID() },
  });
  return res.data;
}
