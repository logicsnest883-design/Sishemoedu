from django.shortcuts import render


def games_home(request):
    return render(request, "games/games_home.html")




from django.shortcuts import render


def quiz_maze(request):
    Q = "Q"
    S = "S"
    F = "F"
    maze = [
        [0, 0, 1, Q, 0, 0],
        [1, 0, 1, 0, 1, 0],
        [0, 0, 0, Q, 1, 0],
        [0, 1, 1, 0, 0, 0],
        [S, 0, Q, 1, 1, F],
    ]

    # we pass a simplified version for JS
    return render(request, "games/quiz_maze.html", {
        "maze_width": 6,
        "maze_height": 5,
    })