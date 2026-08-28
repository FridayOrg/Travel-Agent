Paste the text below into your Lovable project's AI chat.

--------------------------------------------------------------------------------

There is now a backend endpoint for voice input (speech-to-text). Wire up the
microphone/voice button so that whenever the user records audio, it is sent
here for transcription, and the transcribed text is then submitted through
the EXACT SAME unified input path as typed text (the same handler already used
for the chat text box — click / type / voice must all converge on one code
path, per the earlier unified-input-handling prompt).

ENDPOINT

    POST https://travel-agent-mw5e.onrender.com/api/session/{session_id}/stt
    Content-Type: multipart/form-data
    Form field: "audio" — the recorded audio file (wav, mp3, webm, ogg, m4a all work;
    send whatever format the browser's MediaRecorder produces, no client-side
    conversion needed)

    Response: { "text": "<transcribed text>" }

    On error (e.g. invalid/expired session): a non-200 status with { "detail": "..." }.

REQUIRED BEHAVIOR

1. When the user taps the mic button, record audio (MediaRecorder API or
   equivalent), show a clear recording indicator, and let them stop the
   recording (tap again, or auto-stop on silence — either is fine).
2. On stop, POST the recorded audio blob to the /stt endpoint above using the
   session's current session_id.
3. Show a brief "transcribing..." state while waiting (this call can take a
   few seconds).
4. Once the response comes back, take the "text" value and feed it into the
   SAME submit path as if the user had typed it into the chat box and hit
   send — do not create a separate voice-only branch. This means it goes
   through whatever routing already exists for typed text: static-answer
   during a button/form stage, or the normal message endpoint during a free
   conversation stage.
5. If the transcription comes back empty (silence/unintelligible audio),
   don't submit anything — show a small inline message like "Didn't catch
   that, try again" and let them re-record.
6. If the request fails (network error, non-200 response), show a retry
   option rather than failing silently.
7. Use a generous timeout on this request (30+ seconds) — like other backend
   calls, this can be slow on Render's free tier after periods of inactivity
   (cold start).
8. This must work on every screen/stage, not just the free-text chat —
   exactly like typed input, since this is now just another way of feeding
   text into the same unified input handler.
