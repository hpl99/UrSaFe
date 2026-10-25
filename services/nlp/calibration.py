"""
Scientific Probability Calibration Evaluator
Calculates Brier Score and Expected Calibration Error (ECE) to rigorously validate
that estimated confidence aligns with true empirical accuracy.
"""
from typing import List, Dict, Any, Tuple
import math

class CalibrationEvaluator:
    @staticmethod
    def calculate_brier_score(predictions: List[float], ground_truths: List[int]) -> float:
        """
        Calculates the Brier score: Mean squared error between predicted probabilities and binary outcomes.
        Lower is better (0.0 is perfect calibration).
        """
        if not predictions or len(predictions) != len(ground_truths):
            return 1.0

        n = len(predictions)
        total_sq_err = sum((p - y) ** 2 for p, y in zip(predictions, ground_truths))
        return round(total_sq_err / n, 4)

    @staticmethod
    def calculate_expected_calibration_error(
        predictions: List[float],
        ground_truths: List[int],
        num_bins: int = 5,
    ) -> Dict[str, Any]:
        """
        Calculates Expected Calibration Error (ECE):
          ECE = sum( (|B_m| / N) * |acc(B_m) - conf(B_m)| )
        Also returns reliability diagram bin data.
        """
        n = len(predictions)
        if n == 0 or len(predictions) != len(ground_truths):
            return {"ece": 1.0, "bins": []}

        bin_width = 1.0 / num_bins
        bins_data: List[Dict[str, Any]] = []
        total_ece = 0.0

        for b in range(num_bins):
            bin_lower = b * bin_width
            bin_upper = (b + 1) * bin_width

            # Find items belonging to this bin
            bin_indices = [
                i for i, p in enumerate(predictions)
                if (bin_lower <= p < bin_upper) or (b == num_bins - 1 and p == 1.0)
            ]

            bin_count = len(bin_indices)
            if bin_count == 0:
                bins_data.append({
                    "bin_range": f"{bin_lower:.2f}-{bin_upper:.2f}",
                    "count": 0,
                    "accuracy": 0.0,
                    "confidence": 0.0,
                })
                continue

            bin_acc = sum(ground_truths[i] for i in bin_indices) / bin_count
            bin_conf = sum(predictions[i] for i in bin_indices) / bin_count

            ece_contrib = (bin_count / n) * abs(bin_acc - bin_conf)
            total_ece += ece_contrib

            bins_data.append({
                "bin_range": f"{bin_lower:.2f}-{bin_upper:.2f}",
                "count": bin_count,
                "accuracy": round(bin_acc, 3),
                "confidence": round(bin_conf, 3),
            })

        return {
            "ece": round(total_ece, 4),
            "brier_score": CalibrationEvaluator.calculate_brier_score(predictions, ground_truths),
            "sample_count": n,
            "bins": bins_data,
        }
