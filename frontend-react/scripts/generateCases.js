import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const ROOT_DIR = path.resolve(__dirname, '../../');
const ENV_PATH = path.join(__dirname, '../.env'); // changed to frontend-react/.env
const CASES_TXT_PATH = path.join(ROOT_DIR, 'Cases.txt');
const OUT_DIR = path.join(__dirname, '../src/data');
const OUT_PATH = path.join(OUT_DIR, 'cases.json');

// Super simple env parser without dependencies
function loadEnv() {
  if (!fs.existsSync(ENV_PATH)) return {};
  const content = fs.readFileSync(ENV_PATH, 'utf-8');
  return content.split('\n').reduce((acc, line) => {
    const match = line.match(/^\s*([\w.-]+)\s*=\s*(.*)?\s*$/);
    if (match) acc[match[1]] = match[2].replace(/(^['"]|['"]$)/g, '');
    return acc;
  }, {});
}

async function generateCases() {
  const envVars = loadEnv();
  const groqKey = envVars.GROQ_API_KEY || process.env.GROQ_API_KEY;
  const openaiKey = envVars.OPENAI_API_KEY || process.env.OPENAI_API_KEY;

  if (!groqKey && !openaiKey) {
    console.error("Error: Missing GROQ_API_KEY or OPENAI_API_KEY in .env");
    process.exit(1);
  }

  if (!fs.existsSync(CASES_TXT_PATH)) {
    console.error(`Error: Could not find Cases.txt at ${CASES_TXT_PATH}`);
    process.exit(1);
  }

  const rawText = fs.readFileSync(CASES_TXT_PATH, 'utf-8');

  console.log("Found Cases.txt! Processing via LLM...");

  const systemPrompt = `You are a clinical assistant builder. I will give you a list of case scenarios. 
You must analyze the list and return ONLY a valid JSON array of objects securely describing them. 
Do not include markdown \`\`\`json wrappers or any other text before or after the JSON. 

Schema for each object:
{
  "id": Number,
  "title": "String title",
  "subtitle": "Short descriptive clinical string (e.g., Intake Session, Early Intervention)",
  "difficulty": "Beginner, Intermediate, or Advanced",
  "skills": ["Array of", "Exactly 3 short", "Actionable skills"],
  "dynamics": "String format 'BehavioralHint • BehavioralHint' (e.g., Guarded • Avoidant)",
  "objective": "Short summary of the learning goal",
  "duration": "Duration string mapping to complexity (e.g., 10 min, 15 min, 20 min, 25 min, 30 min)"
}`;

  const fetchOptions = groqKey ? {
    url: 'https://api.groq.com/openai/v1/chat/completions',
    headers: { 'Authorization': `Bearer ${groqKey}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model: 'llama-3.3-70b-versatile',
      messages: [{ role: 'system', content: systemPrompt }, { role: 'user', content: rawText }],
      temperature: 0.1,
    })
  } : {
    url: 'https://api.openai.com/v1/chat/completions',
    headers: { 'Authorization': `Bearer ${openaiKey}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model: 'gpt-3.5-turbo',
      messages: [{ role: 'system', content: systemPrompt }, { role: 'user', content: rawText }],
      temperature: 0.1,
    })
  };

  try {
    const response = await fetch(fetchOptions.url, {
      method: 'POST',
      headers: fetchOptions.headers,
      body: fetchOptions.body
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${await response.text()}`);
    }

    const data = await response.json();
    let jsonContent = data.choices[0].message.content.trim();

    // Strip markdown wrapper if the model aggressively included it 
    if (jsonContent.startsWith('```json')) {
      jsonContent = jsonContent.slice(7, -3).trim();
    } else if (jsonContent.startsWith('```')) {
      jsonContent = jsonContent.slice(3, -3).trim();
    }

    if (!fs.existsSync(OUT_DIR)) {
      fs.mkdirSync(OUT_DIR, { recursive: true });
    }

    // Verify it's parsable 
    JSON.parse(jsonContent);

    fs.writeFileSync(OUT_PATH, jsonContent, 'utf-8');
    console.log(`Successfully generated structured case data at ${OUT_PATH}`);

  } catch (error) {
    console.error("Failed to process cases:", error);
    process.exit(1);
  }
}

generateCases();
