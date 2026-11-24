#include "SVShowFXController.h"
#include "SVStyleAsset.h"
#include "SVUILibrary.h"
#include "SVUISettings.h"
#include "SVUISubsystem.h"
#include "NiagaraComponent.h"
#include "Engine/ExponentialHeightFog.h"
#include "Components/ExponentialHeightFogComponent.h"
#include "Engine/LocalPlayer.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"

namespace SVParam
{
	static const FName Spread(TEXT("Spread"));
	static const FName Aim(TEXT("Aim"));
	static const FName Tilt(TEXT("Tilt"));
	static const FName Beat(TEXT("Beat"));
	static const FName Intensity(TEXT("Intensity"));
	static const FName CO2(TEXT("CO2"));
}

ASVShowFXController::ASVShowFXController()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.bTickEvenWhenPaused = true; // the menus can pause the game; the show keeps going

	ModeIntensity.Add(ESVLaserMode::Title, 1.15f);
	ModeIntensity.Add(ESVLaserMode::Menu, 0.55f);
	ModeIntensity.Add(ESVLaserMode::DoorsOpen, 0.8f);
	ModeIntensity.Add(ESVLaserMode::Live, 1.25f);
}

void ASVShowFXController::BeginPlay()
{
	Super::BeginPlay();

	CollectNiagara(LaserActors, Lasers);
	CollectNiagara(CO2Actors, Jets);

	if (Fog && Fog->GetComponent())
	{
		BaseFogDensity = Fog->GetComponent()->FogDensity;
	}
	if (const USVStyleAsset* Style = USVUILibrary::GetStageVerseStyle())
	{
		BPM = Style->MenuBPM;
	}
	bReduceMotion = GetDefault<USVUISettings>()->bReduceMotion;

	if (APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0))
	{
		if (ULocalPlayer* LocalPlayer = PC->GetLocalPlayer())
		{
			if (USVUISubsystem* UI = LocalPlayer->GetSubsystem<USVUISubsystem>())
			{
				UI->RegisterFXController(this);
			}
		}
	}
}

void ASVShowFXController::CollectNiagara(const TArray<TObjectPtr<AActor>>& Actors, TArray<TWeakObjectPtr<UNiagaraComponent>>& Out) const
{
	Out.Reset();
	for (AActor* Actor : Actors)
	{
		if (!Actor)
		{
			continue;
		}
		TArray<UNiagaraComponent*> Components;
		Actor->GetComponents<UNiagaraComponent>(Components);
		for (UNiagaraComponent* Component : Components)
		{
			Out.Add(Component);
		}
	}
}

void ASVShowFXController::SetAimInput(FVector2D NormalizedAim)
{
	TargetAim = FVector2D(FMath::Clamp(NormalizedAim.X, 0.0, 1.0), FMath::Clamp(NormalizedAim.Y, 0.0, 1.0));
}

void ASVShowFXController::SetMode(ESVLaserMode NewMode)
{
	if (const float* Found = ModeIntensity.Find(NewMode))
	{
		TargetIntensity = *Found;
	}
}

void ASVShowFXController::FireCO2()
{
	Burst = 1.f;
	for (const TWeakObjectPtr<UNiagaraComponent>& Jet : Jets)
	{
		if (Jet.IsValid())
		{
			Jet->ResetSystem();
		}
	}
}

void ASVShowFXController::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	// Frame-rate independent easing toward the target aim and intensity.
	const float Follow = 1.f - FMath::Exp(-AimFollowSpeed * DeltaSeconds);
	Aim += (TargetAim - Aim) * Follow;
	Intensity += (TargetIntensity - Intensity) * (1.f - FMath::Exp(-3.f * DeltaSeconds));
	Burst *= FMath::Pow(0.5f, DeltaSeconds / FMath::Max(CO2HalfLife, 0.01f));

	// Sharp pulse on each beat, same curve as the browser prototype.
	const double Seconds = GetWorld() ? GetWorld()->GetRealTimeSeconds() : 0.0;
	const float Phase = static_cast<float>(Seconds * BPM / 60.0);
	const float Beat = bReduceMotion ? 0.f : FMath::Pow(0.5f + 0.5f * FMath::Cos(2.f * PI * Phase), 6.f);

	const float Spread = FMath::Lerp(MinSpread, MaxSpread, static_cast<float>(Aim.X));
	const float AimDeg = static_cast<float>(Aim.X - 0.5) * 2.f * MaxAim;
	const float TiltDeg = static_cast<float>(Aim.Y - 0.5) * 2.f * MaxTilt;

	for (const TWeakObjectPtr<UNiagaraComponent>& Laser : Lasers)
	{
		if (UNiagaraComponent* N = Laser.Get())
		{
			N->SetVariableFloat(SVParam::Spread, Spread);
			N->SetVariableFloat(SVParam::Aim, AimDeg);
			N->SetVariableFloat(SVParam::Tilt, TiltDeg);
			N->SetVariableFloat(SVParam::Beat, Beat);
			N->SetVariableFloat(SVParam::Intensity, Intensity);
			N->SetVariableFloat(SVParam::CO2, Burst);
		}
	}

	if (Fog && Fog->GetComponent() && BaseFogDensity > 0.f)
	{
		Fog->GetComponent()->SetFogDensity(BaseFogDensity * (1.f + Burst * (CO2FogBoost - 1.f)));
	}
}
