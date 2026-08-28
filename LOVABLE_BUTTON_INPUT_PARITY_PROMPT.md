Paste the text below into your Lovable project's AI chat.

--------------------------------------------------------------------------------

I'm working on a travel guide assistant chat app (React-based) that has a step-by-step
conversational flow with clickable suggestion buttons at various points (destination,
traveller type, month, and any other button-based prompts throughout the chat — including
things like "Shall we map out a day-by-day plan?" yes/no buttons, activity suggestions, or
any other interactive button the assistant presents).

CURRENT BUG:
- Clicking any of these buttons works correctly and advances the conversation.
- However, if the user instead TYPES the equivalent answer in the text input, or uses VOICE
  INPUT to say it, it does NOT work — the flow doesn't proceed / the input isn't recognized/handled.

This is NOT limited to destination/traveller type/month — this must be fixed GLOBALLY for every
single button that appears anywhere in this chat flow, present and future.

REQUIRED FIX — APPLY GLOBALLY ACROSS ALL BUTTONS:

1. AUDIT ALL BUTTON INSTANCES
   - Search the entire codebase for every place a suggestion/option/quick-reply button is
     rendered in the chat UI (destination options, traveller type options, month options,
     yes/no confirmations, activity/place suggestions, follow-up prompts, etc.).
   - List them out so we have a full inventory of every clickable button type in the flow.

2. UNIFY INPUT HANDLING GLOBALLY
   - Every button's onClick handler must NOT be a one-off/isolated function. Refactor so ALL
     buttons funnel through ONE shared function, e.g. submitAnswer(value, step) or
     handleUserResponse(value, context).
   - Typing free text and submitting, or using voice input, must call this exact same shared
     function — regardless of which step or which button set is currently displayed.
   - There should be no button anywhere in the app that has its own separate/disconnected logic
     from typed or spoken input.

3. NORMALIZE / MATCH FREE-TEXT & VOICE INPUT TO THE CURRENT STEP'S VALID OPTIONS
   - At any given point in the conversation, the app knows what the valid button options are
     for that step.
   - When the user types or speaks instead of clicking, normalize their input (trim, lowercase,
     fuzzy match / synonym match) against that step's valid options.
   - Examples: if buttons show "Couple", "Family", "Solo", "Friends" and user types/says
     "just me", match to "Solo". If buttons show "Yes" / "No" and user says "sure" or "yeah",
     match to "Yes".
   - If no confident match, have the assistant ask for clarification and re-show the options,
     rather than failing silently or getting stuck.

4. VOICE INPUT MUST WORK END-TO-END, EVERYWHERE
   - Confirm the mic button transcribes speech into text and that the transcribed text goes
     through the SAME normalization + shared handler as typed text, at every step, for every
     button type.

5. REGRESSION-PROOF THIS
   - Since new button-based steps may be added later (e.g. future itinerary options, hotel
     picks, activity picks), structure the solution so any NEW button added automatically
     inherits this behavior — i.e. buttons should be generated from the same config/data
     structure that the input parser also references, not hardcoded separately.

Please locate all button-rendering components, the central conversation-state/flow logic, the
chat text input handler, and the voice input handler. Refactor everything to route through one
shared input-handling path with the matching/normalization layer described above. Show me the
full inventory of buttons found, the specific files you're editing, and a summary of changes
before finalizing.

--------------------------------------------------------------------------------

CONTEXT SPECIFIC TO THIS APP — the exact valid-options contract from the backend, so the
normalization/matching layer validates against real values instead of guessing:

There are two categories of button sets in this app:

A) FIXED, hardcoded option sets (these never change, safe to hardcode as the canonical list
   the matcher checks against):
   - Destination: ["Dubai", "London", "Other"] — "Other" reveals a free-text input; whatever
     is typed there IS the destination (no further matching needed for that one).
   - Traveller type: ["Family", "Friends", "Solo", "Couple"]
   - Month: ["Aug-Sep", "Oct-Nov", "Dec-Jan", "Other"] — same free-text pattern for "Other".
   - Hotel travellers count: ["2 Adults", "2 Adults + 1 Kid", "Other"] — "Other" reveals two
     number inputs (Adults, Kids) instead of matched text.
   - Hotel budget: ["Budget", "Mid-range", "Luxury", "Other"] — "Other" reveals a free-text
     input for a custom budget description.

B) DYNAMIC option sets, sent by the backend at runtime inside the chat reply itself, in this
   exact JSON shape (this is the "clarifying_question" format — see the earlier integration
   prompt for full details):
     {"type": "clarifying_question", "stage": "...", "question": "...", "options": ["...", "..."], "allow_other": true|false}
   The "options" array in THIS message is the canonical valid-answers list for that specific
   turn — trip duration ("2-3 days"/"4-6 days"/"7+ days"/"Other"), itinerary confirmation
   ("Yes, continue"/"Modify itinerary"), hotel style preference, "Are you happy with this
   hotel?" ("Yes, continue"/"Choose another hotel"), and any other clarifying question the
   agent asks — are ALL delivered this same way. Since these options already arrive as data
   (not hardcoded UI), point #5's requirement ("buttons generated from the same config the
   input parser also references") is naturally satisfied here IF the button-rendering code and
   the free-text/voice matcher both read from this same "options" array at runtime, rather than
   the matcher having its own separate hardcoded list for these dynamic steps.

   Important: when an option's label itself means "other"/"something else" (check case-
   insensitively for the substring "other"), typed/voice input should NOT be matched against
   the option list at all — instead treat it as the literal free-text answer, same as clicking
   that "Other" button would.

Whatever text is ultimately resolved (matched option label, or literal free text) gets sent to
the backend exactly the same way a button click would — the backend has no separate code path
for "was this a click, a typed answer, or a voice answer," so nothing else needs to change once
the resolved value reaches the existing submit call for that step.
