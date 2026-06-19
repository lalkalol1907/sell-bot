import { connect, StringCodec } from "nats";

const sc = StringCodec();

export async function publishWorkerSyncChats(natsUrl: string, workerId: number): Promise<void> {
  const nc = await connect({ servers: natsUrl });
  try {
    nc.publish("worker.sync_chats", sc.encode(JSON.stringify({ worker_id: workerId })));
    await nc.flush();
  } finally {
    await nc.close();
  }
}
