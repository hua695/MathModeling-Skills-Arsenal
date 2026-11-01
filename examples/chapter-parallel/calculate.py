"""Reproduce the explicitly synthetic linear-model documentation example."""
import json


def main():
    training = [(x, 2 * x + 1) for x in range(1, 6)]
    mean_x = sum(x for x, _ in training) / len(training)
    mean_y = sum(y for _, y in training) / len(training)
    slope = sum((x - mean_x) * (y - mean_y) for x, y in training) / sum(
        (x - mean_x) ** 2 for x, _ in training
    )
    intercept = mean_y - slope * mean_x
    prediction = slope * 6 + intercept
    print(json.dumps({"data_kind": "synthetic", "training_points": training,
                      "slope": slope, "intercept": intercept, "held_out_x": 6,
                      "held_out_truth": 13, "prediction": prediction,
                      "absolute_error": abs(prediction - 13)}, indent=2))


if __name__ == "__main__":
    main()
