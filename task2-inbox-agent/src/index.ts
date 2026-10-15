import dotenv from "dotenv";
dotenv.config();

import { createServer } from "./api/server";

const PORT = process.env.TASK2_PORT || 8002;
const { app } = createServer();

app.listen(PORT, () => {
  console.log(`[Task 2: Inbox Agent] Service listening on port ${PORT}`);
});
