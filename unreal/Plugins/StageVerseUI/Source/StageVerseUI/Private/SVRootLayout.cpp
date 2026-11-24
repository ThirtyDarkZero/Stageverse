#include "SVRootLayout.h"
#include "SVScreen.h"
#include "SVStyleAsset.h"
#include "SVUILibrary.h"
#include "SVUISettings.h"
#include "SVUISubsystem.h"
#include "Widgets/CommonActivatableWidgetContainer.h"
#include "Kismet/KismetMaterialLibrary.h"
#include "Materials/MaterialParameterCollection.h"
#include "Engine/LocalPlayer.h"

namespace SVFX
{
	static const FName Glitch(TEXT("Glitch"));
	static const FName CO2Flash(TEXT("CO2Flash"));
}

void USVRootLayout::NativeOnInitialized()
{
	Super::NativeOnInitialized();

	FXCollection = GetDefault<USVUISettings>()->FXCollection.LoadSynchronous();

	if (const USVStyleAsset* Style = USVUILibrary::GetStageVerseStyle())
	{
		GlitchDuration = FMath::Max(Style->GlitchCutSeconds, 0.01f);
		FlashDuration = FMath::Max(Style->CO2FlashSeconds, 0.01f);
	}

	if (MenuStack)
	{
		MenuStack->OnDisplayedWidgetChanged().AddUObject(this, &USVRootLayout::HandleDisplayedWidgetChanged);
	}
	if (HudStack)
	{
		HudStack->OnDisplayedWidgetChanged().AddUObject(this, &USVRootLayout::HandleDisplayedWidgetChanged);
	}
}

USVScreen* USVRootLayout::PushScreen(ESVLayer Layer, TSubclassOf<USVScreen> ScreenClass)
{
	if (!ScreenClass)
	{
		return nullptr;
	}
	UCommonActivatableWidgetStack* Stack = Layer == ESVLayer::Hud ? HudStack.Get() : Layer == ESVLayer::Modal ? ModalStack.Get() : MenuStack.Get();
	return Stack ? Stack->AddWidget<USVScreen>(ScreenClass) : nullptr;
}

bool USVRootLayout::PopMenu()
{
	if (!MenuStack || MenuStack->GetNumWidgets() <= 1)
	{
		return false;
	}
	if (UCommonActivatableWidget* Top = MenuStack->GetActiveWidget())
	{
		Top->DeactivateWidget();
		return true;
	}
	return false;
}

void USVRootLayout::ClearMenu()
{
	if (MenuStack)
	{
		MenuStack->ClearWidgets();
	}
}

USVScreen* USVRootLayout::GetTopMenuScreen() const
{
	return MenuStack ? Cast<USVScreen>(MenuStack->GetActiveWidget()) : nullptr;
}

void USVRootLayout::HandleDisplayedWidgetChanged(UCommonActivatableWidget* Widget)
{
	USVScreen* Screen = Cast<USVScreen>(Widget);
	if (!Screen)
	{
		return;
	}

	PlayGlitchCut();

	if (Rail)
	{
		Rail->SetVisibility(Screen->bShowsRail ? ESlateVisibility::SelfHitTestInvisible : ESlateVisibility::Collapsed);
	}

	if (const ULocalPlayer* LocalPlayer = GetOwningLocalPlayer())
	{
		if (USVUISubsystem* UI = LocalPlayer->GetSubsystem<USVUISubsystem>())
		{
			UI->SetLaserMode(Screen->LaserMode);
		}
	}

	OnScreenShown.Broadcast(Screen);
}

void USVRootLayout::PlayGlitchCut()
{
	if (!ShouldReduceMotion())
	{
		GlitchRemaining = GlitchDuration;
	}
}

void USVRootLayout::PlayCO2Flash()
{
	FlashRemaining = ShouldReduceMotion() ? FlashDuration * 0.4f : FlashDuration;
}

void USVRootLayout::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);

	if (GlitchRemaining > 0.f)
	{
		GlitchRemaining = FMath::Max(0.f, GlitchRemaining - InDeltaTime);
		// Stepped, like the prototype's steps(3): full, two-thirds, one-third, off.
		const float Step = FMath::CeilToFloat(3.f * GlitchRemaining / GlitchDuration) / 3.f;
		WriteFX(SVFX::Glitch, Step);
	}
	if (FlashRemaining > 0.f)
	{
		FlashRemaining = FMath::Max(0.f, FlashRemaining - InDeltaTime);
		const float Alpha = FlashRemaining / FlashDuration;
		WriteFX(SVFX::CO2Flash, (ShouldReduceMotion() ? 0.2f : 0.55f) * Alpha * Alpha);
	}
}

void USVRootLayout::WriteFX(FName Param, float Value) const
{
	if (FXCollection)
	{
		UKismetMaterialLibrary::SetScalarParameterValue(this, FXCollection, Param, Value);
	}
}

bool USVRootLayout::ShouldReduceMotion() const
{
	return GetDefault<USVUISettings>()->bReduceMotion;
}
