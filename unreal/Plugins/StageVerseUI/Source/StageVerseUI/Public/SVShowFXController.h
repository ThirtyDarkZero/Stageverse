#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SVTypes.h"
#include "SVShowFXController.generated.h"

class AExponentialHeightFog;
class UNiagaraComponent;

/**
 * Runs the laser rig and CO2 jets behind the menus. Place one in L_FrontEnd and point it at the
 * laser and CO2 actors. It writes these Niagara user parameters on every laser system each frame:
 *   Spread (degrees between beams), Aim (degrees, yaw of the fan), Tilt (degrees),
 *   Beat (0..1 pulse on the BPM), Intensity (0..n, from the laser mode), CO2 (0..1, decays after a blast).
 * The Niagara beam module reads them; the look lives in Niagara, the behaviour lives here.
 *
 * Later the DMX show-control system drives the same rig in a show; this actor then only forwards aim and CO2.
 */
UCLASS(Blueprintable)
class STAGEVERSEUI_API ASVShowFXController : public AActor
{
	GENERATED_BODY()

public:
	ASVShowFXController();

	/** Normalized 0..1 on both axes. X sets aim and spread, Y sets tilt. */
	UFUNCTION(BlueprintCallable, Category = "StageVerse|FX")
	void SetAimInput(FVector2D NormalizedAim);

	UFUNCTION(BlueprintCallable, Category = "StageVerse|FX")
	void SetMode(ESVLaserMode NewMode);

	UFUNCTION(BlueprintCallable, Category = "StageVerse|FX")
	void FireCO2();

	/** Defaults to the style asset's MenuBPM; a show sets its own. */
	UFUNCTION(BlueprintCallable, Category = "StageVerse|FX")
	void SetBPM(float NewBPM) { BPM = FMath::Max(NewBPM, 1.f); }

	/** Actors whose Niagara components are laser emitters. */
	UPROPERTY(EditInstanceOnly, BlueprintReadOnly, Category = "Rig")
	TArray<TObjectPtr<AActor>> LaserActors;

	/** Actors whose Niagara components are CO2 jets (restarted on each blast). */
	UPROPERTY(EditInstanceOnly, BlueprintReadOnly, Category = "Rig")
	TArray<TObjectPtr<AActor>> CO2Actors;

	/** Optional: fog density is raised briefly on a blast so beams punch through the cloud. */
	UPROPERTY(EditInstanceOnly, BlueprintReadOnly, Category = "Rig")
	TObjectPtr<AExponentialHeightFog> Fog;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Feel", meta = (Units = "Degrees"))
	float MinSpread = 2.0f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Feel", meta = (Units = "Degrees"))
	float MaxSpread = 7.5f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Feel", meta = (Units = "Degrees"))
	float MaxAim = 25.0f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Feel", meta = (Units = "Degrees"))
	float MaxTilt = 17.0f;

	/** How fast the heads follow the cursor. Lower feels heavier, like real moving heads. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Feel")
	float AimFollowSpeed = 3.5f;

	/** Seconds for a CO2 blast to fade to half. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Feel", meta = (Units = "s"))
	float CO2HalfLife = 0.45f;

	/** Fog density multiplier at the peak of a blast. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Feel")
	float CO2FogBoost = 2.5f;

	/** Rig intensity per laser mode. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Feel")
	TMap<ESVLaserMode, float> ModeIntensity;

	virtual void Tick(float DeltaSeconds) override;

protected:
	virtual void BeginPlay() override;

private:
	void CollectNiagara(const TArray<TObjectPtr<AActor>>& Actors, TArray<TWeakObjectPtr<UNiagaraComponent>>& Out) const;

	TArray<TWeakObjectPtr<UNiagaraComponent>> Lasers;
	TArray<TWeakObjectPtr<UNiagaraComponent>> Jets;

	FVector2D TargetAim = FVector2D(0.5, 0.5);
	FVector2D Aim = FVector2D(0.5, 0.5);
	float BPM = 128.f;
	float Burst = 0.f;
	float Intensity = 1.f;
	float TargetIntensity = 1.f;
	float BaseFogDensity = 0.f;
	bool bReduceMotion = false;
};
