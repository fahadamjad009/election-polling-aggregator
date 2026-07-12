$ErrorActionPreference = "Stop"

Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)

$steps = @(
    "src\convert_us_data.py",
    "src\clean_polling_data.py",
    "src\build_national_results.py",
    "src\build_national_polling_scope.py",
    "src\build_features.py",
    "src\build_pollster_reliability.py",
    "src\build_similar_elections.py",
    "src\build_train_test_split.py",
    "src\build_model_dataset.py",
    "src\evaluate_baselines.py",
    "src\analyse_development_errors.py",
    "src\evaluate_feature_ablation.py"
)

Write-Host ""
Write-Host "=== DEVELOPMENT PIPELINE START ==="
Write-Host "Project: $PWD"
Write-Host ""

foreach ($step in $steps) {
    Write-Host "------------------------------------------------------------"
    Write-Host "Running: $step"
    Write-Host "------------------------------------------------------------"

    python $step

    if ($LASTEXITCODE -ne 0) {
        throw "Pipeline failed at: $step"
    }

    Write-Host ""
}

Write-Host "------------------------------------------------------------"
Write-Host "Running automated invariant tests"
Write-Host "------------------------------------------------------------"

python -m unittest discover -s tests -p "test_*.py" -v

if ($LASTEXITCODE -ne 0) {
    throw "Automated invariant tests failed."
}

Write-Host ""
Write-Host "=== DEVELOPMENT PIPELINE COMPLETE ==="
Write-Host "All development stages and invariant tests passed."
Write-Host "The final holdout was not evaluated."
Write-Host "Holdout lock preserved:"
Write-Host "data\model\final_holdout\HOLDOUT_EVALUATED.lock"

