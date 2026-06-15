import { SignJWT, jwtVerify } from "jose";

export const JWT_COOKIE_NAME = "sellbot_jwt";

export type JwtPayload = {
  seller_id: number;
  tg_user_id: number;
};

export class JwtSession {
  constructor(
    private secret: string,
    private ttlHours: number,
  ) {}

  private key() {
    return new TextEncoder().encode(this.secret);
  }

  async encode(sellerId: number, tgUserId: number): Promise<string> {
    return new SignJWT({ seller_id: sellerId, tg_user_id: tgUserId })
      .setProtectedHeader({ alg: "HS256" })
      .setExpirationTime(`${this.ttlHours}h`)
      .sign(this.key());
  }

  async decode(token: string | undefined): Promise<JwtPayload | null> {
    if (!token) return null;
    try {
      const { payload } = await jwtVerify(token, this.key());
      const sellerId = Number(payload.seller_id);
      const tgUserId = Number(payload.tg_user_id);
      if (!sellerId) return null;
      return { seller_id: sellerId, tg_user_id: tgUserId };
    } catch {
      return null;
    }
  }
}
