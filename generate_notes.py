"""
Generate structured academic notes from PDF and lecture transcript.

Paste your PDF content and lecture transcript below, then run:
    python generate_notes.py
"""

import sys
import os

# Add parent directory to path to import from openRouter
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))
from openRouter.openrouter import call_openrouter

# =========================
# PASTE YOUR CONTENT HERE
# =========================

pdf = """
## Introduction


## Node.js Authentication - Comprehensive


## Notes


## JWT, Sessions, Cookies & bcrypt Security


## 🎯 Learning Objectives
By the end of this guide, you will understand: Why authentication is necessary in web applications How to securely hash passwords using bcrypt How JWT (JSON Web Tokens) work and when to use them How session-based authentication works with cookies Security best practices for authentication systems Re...

## Part 1: The Foundation - Understanding Authentication


## 1.1 The Core Problem: HTTP is Stateless


## ⚠ The Fundamental Challenge
HTTP protocol is stateless , meaning each request is independent. The server doesn't "remember" previous requests from the same client. Example: If you log in, and then request your profile page, the server has NO IDEA you just logged in!

## 🏦 Real-World Analogy: The Forgetful Bank Teller
Imagine a bank teller with severe amnesia who forgets you after every interaction: You: "Hi, I'd like to check my balance." Teller: "Sure! Can I see your ID?" (verifies) You: "Now I'd like to withdraw $100." Teller: "Who are you? I need to see your ID again!" This is HTTP! Every request needs proof ...

## 1.2 The Solutions
We have two main approaches to solve this problem: Approach How It Works Storage Location Nature Sessions (with Cookies) Server stores user data, sends ID to client Server-side (database/memory) Stateful JWT Tokens Server signs user data, sends to client Client-side (localStorage/cookie) Stateless

## Part 2: Password Security with bcrypt CRITICAL


## 2.1 Why NEVER Store Plain Text Passwords


## ❌ NEVER DO THIS!
// BAD! TERRIBLE! NEVER! const user = { email: "john@example.com", password: 😱 "myPassword123" // PLAIN TEXT! } await database.save(user); Why this is catastrophic: If your database is breached, ALL passwords are exposed Database admins can see passwords Logs might accidentally record passwords User...

## 2.2 Hashing: The One-Way Street


## What is Hashing?
Hashing is a one-way mathematical function that transforms input data into a fixed-length string of characters. Key Properties: 1. Deterministic: Same input always produces same output 2. One-Way: Cannot reverse the process (can't "unhash") 3. Avalanche Effect: Small input change = completely differ...

## 🍳 The Scrambled Egg Analogy
Input: Raw egg (your password) 🥚 Process: Cooking/scrambling (hash function) 🔥 Output: Scrambled egg (hash) 🍽 Critical Point: You CANNOT "unscramble" the egg back to its raw state! Similarly, you cannot "unhash" a password hash.

## 2.3 Enter bcrypt: The Gold Standard


## Why bcrypt?
Salting: Adds random data to prevent rainbow table attacks Slow by Design: Intentionally computationally expensive to prevent brute-force Adaptive: Can increase cost factor as computers get faster Battle-Tested: Industry standard for password hashing

## 2.3.1 Installing bcrypt
npm install bcrypt

## 2.3.2 Hashing a Password (Registration)
const bcrypt = require('bcrypt'); async function registerUser(email, plainPassword) { // Salt rounds: computational cost (10-12 is standard) // Higher = more secure but slower const saltRounds = 10; try { // Hash the password const hashedPassword = await bcrypt.hash(plainPassword, saltRounds); // ha...

## ⚠ Important: Understanding Salt Rounds
Salt Rounds = 2^n iterations Rounds Time (approx) Recommendation ✅ 10 ~100ms Good for most apps 12 ~300ms ✅ High security apps ⚠ 15 ~3 seconds Very slow, use with caution Balance: Higher rounds = more secure but slower login experience

## 2.3.3 Verifying a Password (Login)
const bcrypt = require('bcrypt'); async function loginUser(email, enteredPassword) { try { // 1. Find user in database const user = await database.users.findOne({ email: email }); if (!user) { return { success: false, message: 'Invalid credentials' }; } // 2. Compare entered password with stored has...

## 🎯 How bcrypt.compare() Works
bcrypt.compare() is magical because: 1. It extracts the salt from the stored hash 2. It uses the same salt to hash the entered password 3. It compares the two hashes 4. Returns true if they match, false otherwise You don't need to store the salt separately! It's embedded in the hash.

## 🧠 Brain Teaser
If two users have the same password ("password123"), will their bcrypt hashes be the same?

## Answer: NO!
Each bcrypt hash includes a randomly generated salt, so even identical passwords produce different hashes: User 1: $2b$10$abc123...xyz789 User 2: $2b$10$def456...uvw012 This prevents attackers from identifying users with the same password (rainbow table attack prevention).

## Part 3: JWT (JSON Web Tokens) - Stateless Authentication


## 3.1 What is JWT?


## JWT Definition
JWT (JSON Web Token) is a compact, URL-safe means of representing claims to be transferred between two parties. Think of it as a digitally signed certificate that proves who you are.

## 🎟 The Concert Ticket Analogy
A JWT is like a concert ticket: ✅ Contains information: Your name, seat number, show time (payload) ✅ Signed by the venue: Has a hologram/stamp that can't be forged (signature) ✅ You carry it: You hold the ticket, not the venue (client-side storage) ✅ Show it to enter: Present it each time you need ...

## 3.2 JWT Structure: Three Parts
JWT = HEADER.PAYLOAD.SIGNATURE Example: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiIxMjMiLCJlbWFpbCI6InVzZXJAZXhhbXBsZS5jb20ifQ.4kN7vN0w2Xn └────────── Part 1 ──────────┘ └──────────────── Part 2 ────────────────┘ └──────── Part 3 ────────┘ HEADER PAYLOAD SIGNATURE

## Part 1: HEADER
{ "alg": "HS256", // Algorithm: HMAC SHA-256 "typ": "JWT" // Type: JSON Web Token } This is Base64URL encoded to create the first part of the JWT.

## Part 2: PAYLOAD (Claims)
{ "userId": "12345", "email": "user@example.com", "role": "admin", "iat": 1516239022, // Issued At (timestamp) "exp": 1516242622 // Expiration (timestamp) } This contains the actual data (claims). Also Base64URL encoded .

## ⚠ CRITICAL: Payload is NOT Encrypted!
Anyone can decode the payload. Never put sensitive data like passwords in JWT! Base64 encoding ≠ Encryption. It's just encoding for URL-safe transmission.

## Part 3: SIGNATURE
HMACSHA256( base64UrlEncode(header) + "." + base64UrlEncode(payload), secret_key ) The signature ensures: 1. Integrity: The token hasn't been tampered with 2. Authenticity: It was created by someone with the secret key (your server)

## 3.3 How JWT Authentication Works
JWT Authentication Flow: 1. [User] ─────(Login: email + password)─────> [Server] │ ├─ Verify credentials ├─ Hash password matches? │ 2. [User] <────(JWT Token: "eyJhbGc...")──────── [Server] │ ├─ Store token (localStorage/cookie) │ 3. [User] ─────(Request + JWT in header)──────> [Server] "GET /profi...

## 3.4 Implementing JWT in Node.js


## 3.4.1 Installation
npm install jsonwebtoken bcrypt express dotenv

## 3.4.2 Complete JWT Authentication System
// server.js const express = require('express'); const jwt = require('jsonwebtoken'); const bcrypt = require('bcrypt'); require('dotenv').config(); const app = express(); app.use(express.json()); // In-memory user storage (use database in production) const users = []; // ────────────────────────────...

## 3.4.3 Environment Variables (.env file)
# .env file - NEVER commit this to git! JWT_SECRET=your_super_secret_jwt_key_here_make_it_long_and_random_123456789 PORT=3000

## 🔒 Security Warning
NEVER hardcode secrets in your code! Always use environment variables and add .env to your .gitignore file.

## 3.4.4 Testing the JWT API
# 1. Register a new user curl -X POST http://localhost:3000/register \ -H "Content-Type: application/json" \ -d '{"email":"test@example.com","password":"SecurePass123"}' # Response: {"message":"User registered successfully","userId":1} # 2. Login to get JWT token curl -X POST http://localhost:3000/l...

## Part 4: Session-Based Authentication with Cookies


## 4.1 What are Sessions?


## Session Definition
A session is server-side storage of user state. The server stores user information and gives the client a session ID.

## 🏨 The Hotel Key Card Analogy
Session-based auth is like a hotel: 🎫 Check-in: You register/login (authenticate) 🔑 Key card: Server gives you a session ID (in a cookie) 🏨 Reservation system: Hotel keeps all your details (server-side session store) 🚪 Room access: You show the key card, hotel looks up your reservation 🛎 Services: H...

## 4.2 What are Cookies?


## Cookie Definition
A cookie is a small piece of data (max 4KB) that: ✅ Is stored by the browser ✅ Is sent automatically with every request to the same domain ✅ Can have an expiration date ✅ Can be marked HttpOnly (not accessible via JavaScript - XSS protection) ✅ Can be marked Secure (only sent over HTTPS) ✅ Can be ma...

## 4.3 Session vs JWT Comparison
Aspect Sessions JWT Storage Server-side (database/Redis) Client-side (localStorage/cookie) State Stateful (server remembers) Stateless (server doesn't store) Scalability Harder (need shared session store) Easier (no server storage) Revocation Easy (delete session from DB) Hard (token valid until exp...

## 4.4 Implementing Sessions in Node.js


## 4.4.1 Installation
npm install express-session connect-mongo bcrypt dotenv

## 4.4.2 Complete Session-Based Authentication
// server.js const express = require('express'); const session = require('express-session'); const MongoStore = require('connect-mongo'); const bcrypt = require('bcrypt'); require('dotenv').config(); const app = express(); app.use(express.json()); // ─────────────────────────────────────────────────...

## 4.4.3 Environment Variables for Sessions
# .env SESSION_SECRET=your_super_secret_session_key_make_it_random_and_long MONGODB_URI=mongodb://localhost:27017/myapp PORT=3000 NODE_ENV=development

## Part 5: Security Best Practices CRITICAL


## 5.1 The Security Checklist


## 🛡 Essential Security Measures
1. ✅ Always use HTTPS in production (encrypts data in transit) 2. ✅ Hash passwords with bcrypt (never store plain text) ✅ 3. Store secrets in environment variables (never hardcode) ✅ 4. Use httpOnly cookies (prevent XSS attacks) ✅ 5. Use secure cookies (HTTPS only) ✅ 6. Set SameSite=strict (prevent ...

## 5.2 Rate Limiting Implementation
const rateLimit = require('express-rate-limit'); // Create limiter for authentication endpoints const authLimiter = rateLimit({ windowMs: 15 * 60 * 1000, // 15 minutes max: 5, // Limit each IP to 5 requests per window message: 'Too many attempts, please try again later', standardHeaders: true, // Re...

## 5.3 Input Validation
const { body, validationResult } = require('express-validator'); // Validation middleware const validateRegistration = [ body('email') .isEmail() .normalizeEmail() .withMessage('Valid email required'), body('password') .isLength({ min: 8 }) .withMessage('Password must be at least 8 characters') .mat...

## 5.4 Refresh Token Strategy


## Why Refresh Tokens?
Problem: If an access token is stolen, the attacker has access until it expires. Solution: Use short-lived access tokens (15 min) + long-lived refresh tokens (7 days)

## How It Works:
→ 1. User logs in receives both access token & refresh token 2. Access token used for API requests (expires in 15 min) → 3. When access token expires use refresh token to get new access token 4. Refresh token stored securely (httpOnly cookie or secure storage) 5. If refresh token is compromised → re...

## Part 6: Final Assessment


## 📝 Knowledge Check: Multiple Choice Questions


## Question 1: Password Hashing
Why should you use bcrypt instead of MD5 for password hashing? a) bcrypt is faster b) bcrypt includes automatic salting and is computationally expensive (slow) c) bcrypt produces shorter hashes d) MD5 is deprecated by Node.js Answer: b) bcrypt includes automatic salting and is computationally expens...

## Question 2: JWT Structure
Which part of a JWT ensures the token hasn't been tampered with? a) Header b) Payload c) Signature d) All three parts Answer: c) Signature Explanation: The signature is created by hashing the header and payload with a secret key. Any change to the header or payload will invalidate the signature.

## Question 3: Session Storage
Where is session data primarily stored in session-based authentication? a) Client browser (localStorage) b) JWT token c) Server-side (database or memory) d) URL parameters Answer: c) Server-side (database or memory) Explanation: Sessions are stateful - the server stores user data and gives the clien...

## Question 4: Cookie Flags
What does the "httpOnly" flag do for cookies? a) Makes the cookie only work on HTTP (not HTTPS) b) Prevents JavaScript from accessing the cookie (XSS protection) c) Makes the cookie faster to transmit d) Compresses the cookie data Answer: b) Prevents JavaScript from accessing the cookie Explanation:...

## Question 5: JWT vs Sessions
What is the main advantage of JWT over sessions? a) JWT is more secure b) JWT is stateless (no server-side storage needed) c) JWT can be easily revoked d) JWT tokens are smaller Answer: b) JWT is stateless (no server-side storage needed) Explanation: JWT's main advantage is that the server doesn't n...

## Summary & Decision Guide


## 🎯 When to Use What?


## Use JWT When:
✅ Building APIs for mobile apps ✅ Microservices architecture ✅ Need horizontal scaling ✅ Cross-domain authentication required ✅ Stateless design preferred

## Use Sessions When:
✅ Traditional web applications ✅ Need immediate token revocation ✅ Server-side rendering ✅ Sensitive data in session ✅ Simpler security model preferred

## Best Practice: Hybrid Approach
Many modern apps use both : Short-lived JWT access tokens (15 min) Long-lived refresh tokens stored in httpOnly cookies Refresh tokens tracked in database (can be revoked)

## 🎓 Congratulations!
You now have a comprehensive understanding of Node.js authentication: ✅ Password hashing with bcrypt ✅ JWT token-based authentication ✅ Session-based authentication with cookies ✅ Security best practices ✅ Real-world implementation patterns Next Steps: 1. Build a complete authentication system 2. Im...
"""

lecture = """
Starting with Newton written on the board. Let's take the ASCII values for each character, specifically the last digit of each ASCII code. For "Newton," this yields 897498. This represents the hash value for "Newton." When using Newton, the resulting hash is 897498.  

Hashing is one-way: you cannot reverse it to get the original input. Brute force could match inputs, but collisions are infrequent, making reversal impractical. We use salts instead of initial values to enhance security.  

Recalling last class: JWT tokens have three parts—header, payload, and signature. JWTs come in two types: JWE (encrypted) and JWS (signed). With JWE, you can decrypt the payload and header. With JWS, hashing creates the signature using the header, payload, and secret salt. Both header and payload are Base64-encoded, while the signature is the hash. By default, JWT uses signing (hashing), though encryption is possible.  

Today’s topic is refresh tokens. Consider Instagram’s requirement for persistent user sessions. Issuing a JWT with no expiry poses security risks. The correct approach uses OAuth tokens: an access token (JWT) with 24-hour expiry and a refresh token with 30-day expiry. Upon login, two tokens are generated. After 24 hours of inactivity, the access token expires.

I will check if the user exists and validate the password. Then I will generate two tokens: an access token valid for one minute and a refresh token valid for two minutes, both sent to the client.  

For fetching posts, the token should be in the Authorization header. If no token exists, return unauthorized. If token verification fails through synchronous JWT verification, return unauthorized.  

Testing the login API:  
- Server running on port 3000  
- Received tokens (access: 1 minute, refresh: 2 minutes validity)  

Testing protected post endpoint:  
1. Request without Authorization header: returns "Unauthorized"  
2. Request with expired token: returns "Unauthorized" due to JWT expiration  
3. Request with valid token (used immediately after login): successfully returns dummy post data  

Token management rules:  
- Refresh token should have longer expiry than access token (typically access: 24h, refresh: 30 days in production)  
- Auth flow: Verify token on protected routes. If verification fails (expired/invalid), return "Unauthorized".  

Error handling implemented through try-catch blocks during token verification. The post endpoint returns static dummy data when authentication succeeds.

The payload will match the encoded part, but the signature will not match. Only up to the expiration time will match. The signature does not match the header or payload. This token has expired. To demonstrate refresh tokens, we need another API endpoint: POST /refresh. This will take the refresh token from the header. If the refresh token doesn't exist, return unauthorized. If verified but not valid, return unauthorized. After verification, create new OAuth tokens and a new refresh token, then send them to the frontend.  

First, restart the server. The API requires authorization in the header with no request body. Start the authentication process. After login, the access token expires in one minute while the refresh token remains valid for two minutes. When the access token expires, sending a request returns unauthorized. However, using the valid refresh token generates a new access token valid for another minute. Using this new token grants access to posts again without relogging.  

After two minutes, the refresh token expires and returns unauthorized. After three minutes, nothing works. For permanent login, implement periodic refresh token usage. Typical services like Instagram have 60-day refresh token validity. Google's ecosystem maintains interconnected OAuth across services.  

For authorization middleware, add a role property to the token payload (e.g., 'student' vs 'admin'). The middleware checks the role in the token against required access levels. If the token claims 'student' role but the endpoint requires 'admin', return unauthorized. This is implemented through simple middleware validation.

When the role is admin, upon login, the payload includes roles. Posts can only be accessed by an admin. Middleware requires three parameters: request, token, and next. Here, the payload is extracted. If payload.role is not equal to admin, return a response. Otherwise, proceed to the next function. The middleware handles token authentication first, then user authorization for API access.  

Admin users have privileges to access these APIs. Server restart is required. Tokens are valid for 60 minutes. Testing with a student role results in unauthorized access to posts, as they lack authorization. This is handled in the middleware.  

The task involves building authentication and authorization middleware. Middleware accepts request, response, next. Use function binding to attach extra arguments. For example, binding creates a new function with preset arguments like 1, 2. When called, it executes with these arguments prepended. This principle applies to any function requiring argument binding.

You need to write a very generic middleware which can be used for authentication and authorization for any API with any level of access. OAuth provides authentication systems to third parties. Google built an authentication system and now provides it for others to use. If you log into LinkedIn via Google Sign-In, you're using Google's OAuth system for verification. Multiple OAuth providers exist like Google, Facebook, Apple - their structure is absolutely the same. Learning one provider's implementation allows you to work with others like LinkedIn.

I am ending the quiz. That's it for today. Thank you.

"""

# =========================
# SYSTEM PROMPT
# =========================

SYSTEM_PROMPT = """You are an academic note generation engine.

INPUTS:
- A lecture PDF (authoritative source of syllabus, structure, and definitions).
- A cleaned lecture transcript (secondary source with instructor emphasis).

ABSOLUTE AUTHORITY RULES (MANDATORY):
1. The PDF is the SINGLE source of truth for:
   - Topics
   - Structure
   - Definitions
   - Scope
2. The lecture transcript is SECONDARY and may ONLY:
   - Emphasize importance
   - Clarify existing PDF concepts
   - Add exam-oriented hints explicitly stated by the instructor
3. If the lecture introduces a topic not present in the PDF, IGNORE IT.
4. If the lecture contradicts the PDF, IGNORE THE LECTURE.
5. Do NOT invent topics, examples, definitions, steps, or syllabus structure.

STRUCTURE RULES:
- Follow the PDF's section order exactly.
- Do NOT create new headings.
- Do NOT reorder content.
- Each output section must correspond to a PDF section.

CONTENT RULES:
- Summarize the PDF content first.
- Inject lecture insights ONLY if they clearly reinforce the same PDF section.
- Do NOT merge unrelated lecture explanations.
- Do NOT generalize beyond what is explicitly stated.

STYLE RULES:
- Clean academic notes.
- Concise, exam-oriented language.
- No conversational tone.
- No references to "lecture", "teacher", or "instructor".
- No implementation narration unless present in the PDF.

FAILURE CONDITIONS (DO NOT VIOLATE):
- Including lecture-only topics
- Letting lecture redefine structure
- Hallucinating examples or explanations
- Mixing multiple PDF sections together

OUTPUT:
Structured notes strictly aligned to the PDF, enhanced only where the lecture explicitly adds value."""


# =========================
# GENERATE AND OUTPUT NOTES
# =========================

def generate_notes(pdf_text, lecture_text, model="tngtech/deepseek-r1t2-chimera:free", **kwargs):
    """
    Generate structured academic notes from PDF and lecture transcript.
    """
    if not pdf_text or not pdf_text.strip():
        raise ValueError("PDF text cannot be empty")
    
    if not lecture_text or not lecture_text.strip():
        raise ValueError("Lecture text cannot be empty")
    
    # Construct user message with both inputs
    user_message = f"""PDF CONTENT (AUTHORITATIVE SOURCE):
{pdf_text}

---

LECTURE TRANSCRIPT (SECONDARY SOURCE):
{lecture_text}

---

Generate structured academic notes following the PDF structure, enhanced only where the lecture explicitly adds value."""
    
    # Call LLM with system prompt
    notes = call_openrouter(
        message=user_message,
        model=model,
        system_prompt=SYSTEM_PROMPT,
        **kwargs
    )
    
    return notes


if __name__ == "__main__":
    print("Generating notes...")
    try:
        notes = generate_notes(pdf, lecture)
        print("\n" + "="*80)
        print("GENERATED NOTES")
        print("="*80)
        print(notes)
        print("="*80)
    except Exception as e:
        print(f"\n✗ Error generating notes: {e}", file=sys.stderr)
        sys.exit(1)
