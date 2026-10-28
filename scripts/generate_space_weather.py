
    lines = [
        colored("宇宙天気", "#66CCFF"),
        f"Kp指数: {colored(f'{kp:.2f}', '#FFFFFF')}",
        f"状態: {colored(status, status_color)}",
        f"太陽活動: {colored(solar, solar_color)}",
        "",
        "",
        (
            "<align=right><size=60%>"
            + colored(
                "観測: " + observation_time.strftime("%Y-%m-%d %H:%M") + " UTC",
                "#BBBBBB"
            )
            + "</size></align>"
        ),
    ]

