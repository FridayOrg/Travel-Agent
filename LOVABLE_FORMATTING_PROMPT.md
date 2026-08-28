Paste the text below into your Lovable project's AI chat.

--------------------------------------------------------------------------------

Update the chat message rendering so AI replies from the travel assistant are properly
formatted instead of showing raw markdown characters. Three things to fix:

1. MARKDOWN BOLD MUST ACTUALLY RENDER
   Right now `**text**` shows literally with the asterisks visible instead of being bold.
   Parse standard markdown bold (`**text**`) in every AI chat message and render it as real
   bold text (e.g. `<strong>` or a bold font-weight span) — not raw asterisks.

2. A SPECIAL ##...## MARKER MUST RENDER AS A HIGHLIGHTED QUESTION
   The backend now wraps a reply's closing call-to-action question (when it has one) in double
   hashes instead of asterisks, like this:
     ##Shall we map out a day-by-day plan for your trip?##
   Parse this `##...##` pattern (distinct from `**...**` bold) and render just that phrase as a
   visually distinct highlighted element — bold text inside a colored pill/box with rounded
   corners and an accent background (use whatever accent color this app's design system already
   uses), clearly set apart from the rest of the message. Strip the `##` markers themselves from
   the displayed text.

3. DO NOT BREAK THE EXISTING clarifying_question / booking_form JSON HANDLING
   Some replies are ONLY a JSON object (starting with `{"type": "clarifying_question", ...}` or
   exactly `{"type": "booking_form"}`) and are already handled separately as buttons/forms, not
   as prose. The bold/`##` parsing above only applies to normal prose replies — don't run it on
   messages that are JSON-only, and don't let JSON-only messages fall through to the bold/##
   parser and get corrupted.

Example of a reply that needs correct rendering (bold on place names, highlighted pill on the
closing question):

  Welcome to Dubai! October and November are absolute perfection for a couple's getaway...
  iconic spots like **Global Village** open for the season.

  For a romantic trip, you might love strolling hand-in-hand around **Burj Park** for the
  evening fountain lights, heading out to the peaceful heart-shaped **Love Lake** in Al Qudra...

  ##Shall we map out a day-by-day plan for your trip?##

"Global Village", "Burj Park", and "Love Lake" should render bold. The last line should render
as a highlighted pill/box, not plain bold text, with the ## markers removed from what's shown.

--------------------------------------------------------------------------------

SEPARATE ISSUE — also worth fixing while you're in this code:

If you're seeing an error like "Sorry — I could not reach the travel service. Failed to fetch"
on the first message after the app has been idle for a while, that's very likely a client-side
fetch timeout that's too short. The backend runs on Render's free tier, which sleeps after ~15
minutes of no traffic — the first request after that can take 30-60 seconds to wake up, and
heavier requests (hotel search, multi-step chat turns) can occasionally take several minutes
under free-tier rate limits. Make sure the fetch calls to the backend use a generous timeout
(5+ minutes) rather than a short default, and show a "still thinking..." loading state instead
of failing fast — don't treat a slow response as an error until well past that window.
