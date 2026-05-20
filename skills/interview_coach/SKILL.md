# Interview Coach

## Purpose

This skill standardizes the coaching and feedback style after a mock interview session.

Use it when:

- the interview is completed
- the agent needs to summarize strengths and weaknesses
- the system should produce consistent coaching output
- recommendations must be phrased as actionable drills instead of vague advice

## Triggers

Activate this skill when at least one of the following is true:

- the workflow enters the final report node
- the agent has collected answer evaluations across one or more turns
- the user asks for coaching, feedback, summary, or improvement plan

## Behaviour

When active, the agent should:

1. summarize what the candidate did well
2. name the weakest parts of the session
3. convert detected gaps into specific improvement advice
4. recommend concrete drills or repetition topics
5. keep tone supportive, direct, and practical

## Constraints

- do not invent strengths that are unsupported by the session
- do not hide weak areas behind generic praise
- do not output an unstructured wall of text
- recommendations must be specific enough to practice

## Expected Output Format

Return coaching in the following structure:

### What was good
- concise strengths grounded in the interview

### What was weak
- concrete weaknesses or missing signals

### How to improve
- direct actions the candidate should take

### Recommended drills
- 2-4 targeted practice items or topics

## Example Usage

If the candidate gave relevant answers but missed trade-offs and examples, the report should:

- praise relevance and baseline technical understanding
- call out missing project detail and weak trade-off explanation
- suggest retelling answers with context, decision, trade-off, result
- recommend drills on project deep dives and follow-up practice
