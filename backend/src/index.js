const dotenv = require("dotenv");
const { createApp } = require("./app");

dotenv.config();

const port = Number(process.env.PORT || 3000);
const aiServiceUrl = process.env.AI_SERVICE_URL || "http://localhost:8000";

const app = createApp({ aiServiceUrl });

app.listen(port, () => {
  console.log(`Backend running on port ${port}`);
  console.log(`AI service target: ${aiServiceUrl}`);
});
