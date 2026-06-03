# Sprint 1 Input Video Source Manifest

Purpose: strengthen Sprint 1 coverage beyond the existing running/sprinting video by adding missing athletic actions from the PDF: jumping and cutting/change-of-direction.

Current local video already used:

| Action | Local file | Status |
| --- | --- | --- |
| Running / sprinting | `sprint1/input_videos/special_olympics_running.webm` | Present and processed |

Recommended additional public videos:

| Action | Target local file | Source page | Download URL |
| --- | --- | --- | --- |
| Jumping / rapidity test | `sprint1/input_videos/jump_rapidity_test.ogv` | `https://commons.wikimedia.org/wiki/File:Analysis-of-Balance-Rapidity-Force-and-Reaction-Times-of-Soccer-Players-at-Different-Levels-of-pone.0077264.s007.ogv` | `https://commons.wikimedia.org/wiki/Special:Redirect/file/Analysis-of-Balance-Rapidity-Force-and-Reaction-Times-of-Soccer-Players-at-Different-Levels-of-pone.0077264.s007.ogv` |
| Cutting / side-step movement | `sprint1/input_videos/rugby_side_step_cutting.ogv` | `https://commons.wikimedia.org/wiki/File:Detecting-Deception-in-Movement-The-Case-of-the-Side-Step-in-Rugby-pone.0037494.s001.ogv` | `https://commons.wikimedia.org/wiki/Special:Redirect/file/Detecting-Deception-in-Movement-The-Case-of-the-Side-Step-in-Rugby-pone.0037494.s001.ogv` |
| Soccer change-of-direction dribble | `sprint1/input_videos/soccer_scissors_dribble.ogv` | `https://commons.wikimedia.org/wiki/File:Scissors_soccer.theora.ogv` | `https://commons.wikimedia.org/wiki/Special:Redirect/file/Scissors%20soccer.theora.ogv` |

Notes:

- The Codex sandbox could view these source pages but could not download the files directly because outbound shell network access was blocked.
- Run `sprint1/download_action_videos.ps1` from PowerShell on your machine to download them.
- Then run `sprint1/process_action_video_suite.ps1` to rerun Sprint 1 on every available action video.
- These videos improve action coverage. They do not create true synchronized multi-angle processing.
