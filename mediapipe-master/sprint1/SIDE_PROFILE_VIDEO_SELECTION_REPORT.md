# Side-Profile Video Selection Report

## Goal

Find better Sprint 1 input videos with a single athlete, side-profile or third-person camera angle, and enough full-body visibility for biomechanical analysis.

## Best Usable Clips

### 1. Side View Running In Place

- Input video: `sprint1/input_videos/side_view_woman_running_in_place_10042798.mp4`
- Overlay output: `sprint1/outputs/side_view_woman_running_in_place_10042798_enhanced_overlay.mp4`
- CSV output: `sprint1/outputs/side_view_woman_running_in_place_10042798_enhanced.csv`
- Summary: `sprint1/outputs/side_view_woman_running_in_place_10042798_enhanced_summary.md`
- Pose coverage: 344 / 344 frames, 100.0%
- Assessment: Best side-profile single-athlete clip. Full body is visible and pose tracking is stable. This is the safest video for Sprint 1 biomechanical demonstration, although it is running-in-place rather than track sprinting.

### 2. Side View Hurdling / Jumping

- Input video: `sprint1/input_videos/athlete_hurdling_side_30997023.mp4`
- Overlay output: `sprint1/outputs/athlete_hurdling_side_30997023_enhanced_overlay.mp4`
- CSV output: `sprint1/outputs/athlete_hurdling_side_30997023_enhanced.csv`
- Summary: `sprint1/outputs/athlete_hurdling_side_30997023_enhanced_summary.md`
- Pose coverage: 141 / 254 frames, 55.5%
- Assessment: Best side-profile jumping/hurdling clip. It gives a realistic third-person sports view, but the athlete is smaller in frame, so pose coverage is lower than the running-in-place clip.

### 3. Track Sprinting, Low Third-Person View

- Input video: `sprint1/input_videos/athlete_sprinting_track_32259382.mp4`
- Overlay output: `sprint1/outputs/athlete_sprinting_track_32259382_enhanced_overlay.mp4`
- CSV output: `sprint1/outputs/athlete_sprinting_track_32259382_enhanced.csv`
- Summary: `sprint1/outputs/athlete_sprinting_track_32259382_enhanced_summary.md`
- Pose coverage: 280 / 289 frames, 96.9%
- Assessment: Good professional track clip with strong pose coverage, but it is more rear/third-person than side-profile. Useful as a secondary Sprint 1 sample, not the main side-view sample.

## Rejected or Weak Clips

### side_view_runner_rural_11966895.mp4

- Pose coverage: 42 / 405 frames, 10.4%
- Reason: Athlete is too far away for reliable biomechanical tracking.

### track_runner_side_8533785.mp4

- Pose coverage: 117 / 314 frames, 37.3%
- Reason: Too cropped and close-up. Not enough full-body visibility.

### track_jogging_side_8533111.mp4

- Pose coverage: 446 / 465 frames, 95.9%
- Reason: High tracking coverage, but the video is mostly upper-body/face close-up, so it is not useful for knee, hip, and ankle biomechanics.

### runner_track_daytime_32240945.mp4

- Pose coverage: 564 / 761 frames, 74.1%
- Reason: Low ground/rear view. Legs are partially visible, but the angle is not ideal for side-profile analysis.

### track_start_side_8533117.mp4

- Pose coverage: 682 / 1066 frames, 64.0%
- Reason: Mostly close-up starting-position shots. Not a clean full-body running or jumping sample.

## Recommendation

Use this as the main Sprint 1 video:

`sprint1/input_videos/side_view_woman_running_in_place_10042798.mp4`

Use this as the jumping/hurdling supplement:

`sprint1/input_videos/athlete_hurdling_side_30997023.mp4`

Use this only as an extra track-running sample:

`sprint1/input_videos/athlete_sprinting_track_32259382.mp4`

## Contact Sheet

Visual comparison file:

`sprint1/outputs/side_profile_candidate_contact_sheet.jpg`
