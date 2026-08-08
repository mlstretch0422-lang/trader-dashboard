const token = process.env.DISCORD_BOT_TOKEN;
if (!token) throw new Error("DISCORD_BOT_TOKEN is required");

const API = "https://discord.com/api/v10";
const AVATAR_PNG_BASE64 = "iVBORw0KGgoAAAANSUhEUgAAAIAAAACACAYAAADDPmHLAAAB40lEQVR42u3cu23DMBRAUflBtQt3zhautIbmyECZI2ukyhZZw2kN5AMkkMRHvnPLIB+TPKAi2/TpfLneJ5UtTAEAAkAACAABIAAEgAAQAAJAAAgAASAABIAAEAACQAAIAAEgAASAAFCfzUf8kdvzx5evvb88mf0E8xQtBvXb1y3+sfMULQYFQZ55ilaDgiDHPEXLQVVHkGGe3AW4DRQAAkAACAABIAAEgAAQAAJAYzdneBDrMk3rUvMFodc3O4AAEAACQAAIAAGgWs8DZLr3XhcAyi36T99XAUNY/O1/DoABFr8KgrD4tRHMWRZq61OwW5+i6eEx2gF2ntgRj7CFxa+NwBNBxQMAANt/5cuAHcAOIAAEgAAQAAKg44769NGRPuXUDmAHEAAuAyW3/2F3gL0WacRPOB/6dPCW7+Tp4THaAb5ZtEy/xyWgQwSjvzW8xF3AfxexwrmAMgdDHhfTyaCCACovcvlLgAAQAAJAAAgAAaBUzwPscfK2h5wOFgACQAAIAAEgAASAABAAAkAAqEsAf31hp+ILQVnmKVoPruriZ5mnaDm46oufYZ6i1eAsfo55Op0v17vp90+gABAAAkAACAABIAAEgAAQAAJAAAgAASAABIAAEAACQAAIAAEgANRfnz2qd7otUQgXAAAAAElFTkSuQmCC";
const avatar = `data:image/png;base64,${AVATAR_PNG_BASE64}`;

async function patch(path, body) {
  const response = await fetch(`${API}${path}`, {
    method: "PATCH",
    headers: {
      authorization: `Bot ${token}`,
      "content-type": "application/json",
      "user-agent": "SignalBridgeBrandSync/1.0",
    },
    body: JSON.stringify(body),
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(`Discord brand sync failed at ${path}: HTTP ${response.status} ${JSON.stringify(payload)}`);
  }
  return payload;
}

const bot = await patch("/users/@me", {
  username: "Signal Bridge",
  avatar,
});

const app = await patch("/applications/@me", {
  description: "Signal Bridge trading desk: session briefs, market intelligence, ORB state, trade journaling, and Discord-linked member access.",
});

console.log(`Signal Bridge bot branding synced: ${bot.username || "Signal Bridge"}`);
console.log(`Signal Bridge application description synced (${String(app.description || "").length} chars).`);
