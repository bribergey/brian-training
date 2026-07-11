import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const RESEND_API_URL = "https://api.resend.com/emails";
const NOTIFICATION_TO = "bbergey@gmail.com";
const NOTIFICATION_FROM = "Briq Training <reviews@lostplatefoodtours.com>";

type InvitationRecord = {
  id: string;
  name: string;
  email: string;
  source: string;
  status: string;
  created_at: string;
  notified_at: string | null;
};

type InvitationWebhook = {
  type: string;
  table: string;
  schema: string;
  record: InvitationRecord;
  old_record: null;
};

function jsonResponse(body: Record<string, unknown>, status = 200): Response {
  return Response.json(body, { status });
}

function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function secretsMatch(
  received: string,
  expected: string,
): Promise<boolean> {
  const encoder = new TextEncoder();
  const [receivedHash, expectedHash] = await Promise.all([
    crypto.subtle.digest("SHA-256", encoder.encode(received)),
    crypto.subtle.digest("SHA-256", encoder.encode(expected)),
  ]);
  const receivedBytes = new Uint8Array(receivedHash);
  const expectedBytes = new Uint8Array(expectedHash);
  return receivedBytes.every((value, index) => value === expectedBytes[index]);
}

function isValidPayload(payload: InvitationWebhook): boolean {
  const record = payload?.record;
  return payload?.type === "INSERT" &&
    payload?.schema === "training" &&
    payload?.table === "invitation_requests" &&
    typeof record?.id === "string" &&
    typeof record?.name === "string" &&
    record.name.length > 0 &&
    record.name.length <= 120 &&
    typeof record?.email === "string" &&
    record.email.length >= 3 &&
    record.email.length <= 320 &&
    record.source === "marketing_home" &&
    record.status === "new" &&
    record.notified_at === null;
}

Deno.serve(async (request) => {
  if (request.method !== "POST") {
    return jsonResponse({ error: "Method not allowed" }, 405);
  }

  const expectedSecret = Deno.env.get("INVITE_WEBHOOK_SECRET");
  const resendApiKey = Deno.env.get("RESEND_API_KEY");
  const receivedSecret = request.headers.get("x-invite-webhook-secret") || "";
  if (!expectedSecret || !resendApiKey) {
    console.error("Invitation notification secrets are not configured");
    return jsonResponse({ error: "Notification service unavailable" }, 503);
  }
  if (
    !receivedSecret || !(await secretsMatch(receivedSecret, expectedSecret))
  ) {
    return jsonResponse({ error: "Unauthorized" }, 401);
  }

  let payload: InvitationWebhook;
  try {
    payload = await request.json();
  } catch {
    return jsonResponse({ error: "Invalid JSON" }, 400);
  }
  if (!isValidPayload(payload)) {
    return jsonResponse({ error: "Invalid invitation event" }, 400);
  }

  const { record } = payload;
  const createdAt = new Date(record.created_at);
  const createdLabel = Number.isNaN(createdAt.getTime())
    ? record.created_at
    : createdAt.toISOString();
  const text = [
    "A new Briq Training invitation was requested.",
    "",
    `Name: ${record.name}`,
    `Email: ${record.email}`,
    `Requested: ${createdLabel}`,
  ].join("\n");
  const html = `
    <h2>New Briq Training invitation request</h2>
    <p><strong>Name:</strong> ${escapeHtml(record.name)}</p>
    <p><strong>Email:</strong> ${escapeHtml(record.email)}</p>
    <p><strong>Requested:</strong> ${escapeHtml(createdLabel)}</p>
  `;

  const resendResponse = await fetch(RESEND_API_URL, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${resendApiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      from: NOTIFICATION_FROM,
      to: [NOTIFICATION_TO],
      reply_to: record.email,
      subject: "New Briq Training invitation request",
      text,
      html,
    }),
  });
  if (!resendResponse.ok) {
    console.error(
      `Resend invitation notification failed with ${resendResponse.status}`,
    );
    return jsonResponse({ error: "Email delivery failed" }, 502);
  }

  return jsonResponse({ delivered: true });
});
