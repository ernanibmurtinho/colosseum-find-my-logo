"""Command-line interface for logo-finder."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from logo_finder.animator import animate_zoom
from logo_finder.enhance import crop_and_upscale
from logo_finder.matcher import find_logo


def _add_common_match_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("logo", type=Path, help="Path to the logo (template) image")
    parser.add_argument("mosaic", type=Path, help="Path to the mosaic image to search")
    parser.add_argument("--min-scale", type=int, default=50,
                        help="Smallest template size to try, in pixels (default: 50)")
    parser.add_argument("--max-scale", type=int, default=110,
                        help="Largest template size to try, exclusive (default: 110)")
    parser.add_argument("--scale-step", type=int, default=2,
                        help="Step between scale attempts (default: 2)")


def cmd_find(args: argparse.Namespace) -> int:
    matches = find_logo(
        args.logo, args.mosaic,
        min_scale=args.min_scale, max_scale=args.max_scale, scale_step=args.scale_step,
        top_n=args.top_n,
    )
    if args.top_n == 1:
        m = matches  # type: ignore[assignment]
        print(f"confidence={m.confidence:.3f}  size={m.size}px  "
              f"top_left=({m.x}, {m.y})  center={m.center}")
    else:
        for i, m in enumerate(matches, 1):  # type: ignore[union-attr]
            print(f"#{i}  confidence={m.confidence:.3f}  size={m.size}px  "
                  f"top_left=({m.x}, {m.y})  center={m.center}")
    return 0


def cmd_enhance(args: argparse.Namespace) -> int:
    match = crop_and_upscale(
        args.logo, args.mosaic, args.output,
        target_size=args.size, padding=args.padding,
    )
    print(f"Wrote {args.output} (matched at {match.center} with confidence {match.confidence:.3f})")
    return 0


def cmd_animate(args: argparse.Namespace) -> int:
    if args.output is None and args.gif is None:
        print("error: provide at least one of -o/--output or --gif", file=sys.stderr)
        return 2
    match = animate_zoom(
        args.logo, args.mosaic,
        mp4_path=args.output, gif_path=args.gif,
        fps=args.fps, duration_seconds=args.duration,
        hold_start_seconds=args.hold_start, hold_end_seconds=args.hold_end,
        output_size=args.size, end_size=args.end_size,
    )
    outputs = [p for p in (args.output, args.gif) if p is not None]
    print(f"Wrote {', '.join(str(p) for p in outputs)} "
          f"(matched at {match.center} with confidence {match.confidence:.3f})")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="logo-finder",
        description="Find a logo in a mosaic of icons.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_find = sub.add_parser("find", help="Locate the logo and print coordinates")
    _add_common_match_args(p_find)
    p_find.add_argument("-n", "--top-n", type=int, default=1,
                        help="Return the top N distinct matches (default: 1)")
    p_find.set_defaults(func=cmd_find)

    p_enhance = sub.add_parser("enhance", help="Crop the matched region and upscale it")
    _add_common_match_args(p_enhance)
    p_enhance.add_argument("-o", "--output", type=Path, required=True,
                           help="Output image path")
    p_enhance.add_argument("--size", type=int, default=1024,
                           help="Side length of the (square) output in pixels (default: 1024)")
    p_enhance.add_argument("--padding", type=int, default=0,
                           help="Extra source pixels to include around the match (default: 0)")
    p_enhance.set_defaults(func=cmd_enhance)

    p_anim = sub.add_parser("animate", help="Render a zoom-in animation")
    _add_common_match_args(p_anim)
    p_anim.add_argument("-o", "--output", type=Path, default=None,
                        help="Output MP4 path")
    p_anim.add_argument("--gif", type=Path, default=None,
                        help="Output GIF path")
    p_anim.add_argument("--size", type=int, default=720,
                        help="MP4 output side length (default: 720)")
    p_anim.add_argument("--fps", type=int, default=30, help="MP4 frame rate (default: 30)")
    p_anim.add_argument("--duration", type=float, default=3.5,
                        help="Total animation duration in seconds (default: 3.5)")
    p_anim.add_argument("--hold-start", type=float, default=0.4,
                        help="Seconds to hold on full mosaic (default: 0.4)")
    p_anim.add_argument("--hold-end", type=float, default=1.0,
                        help="Seconds to hold on the logo (default: 1.0)")
    p_anim.add_argument("--end-size", type=int, default=120,
                        help="Final viewport size in source pixels (default: 120)")
    p_anim.set_defaults(func=cmd_animate)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
