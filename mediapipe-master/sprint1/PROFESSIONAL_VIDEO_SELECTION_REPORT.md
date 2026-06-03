# Sprint 1 Professional Video Selection Report

Goal: replace weak public clips with professional-level athlete videos suitable for Sprint 1 biomechanics analysis.

## Downloaded Professional Videos

| Action | Local video | Source | Pose coverage | Decision |
| --- | --- | --- | ---: | --- |
| Track running | `sprint1/input_videos/pro_track_running_male_8533150.mp4` | Pexels video 8533150 | 86.0% | Use as professional running backup |
| Sprint start / track running | `sprint1/input_videos/pro_track_sprint_start_8533476.mp4` | Pexels video 8533476 | 95.8% | Recommended professional sprint video |
| Long jump | `sprint1/input_videos/pro_long_jump_31229030.mp4` | Pexels video 31229030 | 98.0% | Recommended professional jumping video |
| Young athlete long jump | `sprint1/input_videos/pro_young_long_jump_35377304.mp4` | Pexels video 35377304 | 100.0% | Best pose coverage for jumping |
| Track running candidate | `sprint1/input_videos/pro_track_running_male_8533152.mp4` | Pexels video 8533152 | 20.6% | Not recommended |

## Existing Main Video

| Action | Local video | Pose coverage | Decision |
| --- | --- | ---: | --- |
| Running / sprinting | `sprint1/input_videos/special_olympics_running.webm` | 98.3% | Still valid and high quality |

## Recommended Sprint 1 Evidence Set

Use these as the Sprint 1 evidence videos:

1. `sprint1/input_videos/special_olympics_running.webm`
2. `sprint1/input_videos/pro_track_sprint_start_8533476.mp4`
3. `sprint1/input_videos/pro_long_jump_31229030.mp4`
4. `sprint1/input_videos/pro_young_long_jump_35377304.mp4`

This gives Sprint 1 stronger coverage of:

- running / sprinting
- sprint start / acceleration posture
- long jump / jumping mechanics

## Processed Outputs

Professional sprint start:

- `sprint1/outputs/pro_track_sprint_start_8533476_enhanced.csv`
- `sprint1/outputs/pro_track_sprint_start_8533476_enhanced_overlay.mp4`
- `sprint1/outputs/pro_track_sprint_start_8533476_enhanced_summary.md`

Professional long jump:

- `sprint1/outputs/pro_long_jump_31229030_enhanced.csv`
- `sprint1/outputs/pro_long_jump_31229030_enhanced_overlay.mp4`
- `sprint1/outputs/pro_long_jump_31229030_enhanced_summary.md`

Young athlete long jump:

- `sprint1/outputs/pro_young_long_jump_35377304_enhanced.csv`
- `sprint1/outputs/pro_young_long_jump_35377304_enhanced_overlay.mp4`
- `sprint1/outputs/pro_young_long_jump_35377304_enhanced_summary.md`

## Important Note

These videos improve Sprint 1 action coverage and presentation quality. They do not create true synchronized multi-angle processing. Multi-angle analysis would still require two or more synchronized camera views of the same athlete action.
