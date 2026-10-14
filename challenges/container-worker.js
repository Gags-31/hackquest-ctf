// HackQuest CTF - Cloudflare Worker entrypoint.
// All traffic is proxied to the Flask container. No logic lives here,
// so the app behaves exactly as it does on Render.

import { DurableObject } from "cloudflare:workers";

export class Container extends DurableObject {
  constructor(ctx, env) {
    super(ctx, env);
    ctx.blockConcurrencyWhile(async () => {
      await this.ctx.container.start({
        envVars: {
          PORT: "8080",
          SECRET_KEY: env.SECRET_KEY,
          ADMIN_TOKEN: env.ADMIN_TOKEN,
        },
      });
    });
  }

  fetch(request) {
    return this.ctx.container.fetch(request);
  }
}

export default {
  async fetch(request, env) {
    let id = env.CONTAINER.idFromName("hackquest-singleton");
    return env.CONTAINER.get(id).fetch(request);
  },
};