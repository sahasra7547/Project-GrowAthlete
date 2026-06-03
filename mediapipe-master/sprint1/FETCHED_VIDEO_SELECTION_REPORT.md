# Sprint 1 Fetched Video Selection Report

Goal: fetch a more relevant public video for Sprint 1 and test whether it is useful for MediaPipe pose analysis.

## Videos Fetched And Tested

| Candidate | Local input video | Action fit | Pose coverage | Decision |
| --- | --- | --- | ---: | --- |
| Existing Special Olympics running video | `sprint1/input_videos/special_olympics_running.webm` | Strong running/sprinting fit | 98.3% | Best main Sprint 1 video |
| Jogging near Arakawa river, Tokyo | `sprint1/input_videos/jogging_arakawa_tokyo.webm` | Relevant single-person jogging/running footage | 78.0% | Useful backup/reference video |
| Marine Park jogging path | `sprint1/input_videos/marine_park_jogging_path.webm` | Jogging-path footage, but pose visibility is weak | 16.2% | Not recommended |
| Warrior fitness | `sprint1/input_videos/warrior_fitness.webm` | Fitness/training footage, less aligned with single-athlete running analysis | 79.7% | Optional only, not main evidence |

## Recommended Sprint 1 Choice

Use the existing Special Olympics running video as the main Sprint 1 evidence:

`sprint1/input_videos/special_olympics_running.webm`

Reason:

- Highest pose-detection coverage: 98.3%.
- Clear single-athlete running/sprinting motion.
- Best output quality for knee, hip, and ankle biomechanics.

## Best Newly Fetched Backup Video

Use this only as a secondary/backup video:

`sprint1/input_videos/jogging_arakawa_tokyo.webm`

Converted MP4 for easier viewing:

`sprint1/input_videos/jogging_arakawa_tokyo.mp4`

Processed outputs:

- `sprint1/outputs/jogging_arakawa_tokyo_enhanced.csv`
- `sprint1/outputs/jogging_arakawa_tokyo_enhanced_overlay.mp4`
- `sprint1/outputs/jogging_arakawa_tokyo_enhanced_summary.md`

## Source

Jogging near Arakawa river, Tokyo:

`https://commons.wikimedia.org/wiki/Special:Redirect/file/Jogging%20-%20near%20arakawa%20river%20-%20tokyo%20japan%20-%202022%20may%203.webm`

## Final Note

The fetched jogging video improves the project backup dataset, but it should not replace the current main Sprint 1 video because the current main video has much better pose coverage and cleaner biomechanics output.
