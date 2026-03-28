import "dotenv/config";
import app from "./app.js";

const PORT = Number(process.env.PORT || 3000);
const AI_SERVICE_URL = process.env.AI_SERVICE_URL || "http://localhost:8000";

app.listen(PORT, () => {
  console.log(`Backend running on port ${PORT}`);
  console.log(`AI service target: ${AI_SERVICE_URL}`);
});
