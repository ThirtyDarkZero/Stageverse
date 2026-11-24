#include "SVUISubsystem.h"
#include "SVRootLayout.h"
#include "SVScreen.h"
#include "SVShowFXController.h"
#include "SVUISettings.h"
#include "Blueprint/UserWidget.h"
#include "GameFramework/PlayerController.h"

DEFINE_LOG_CATEGORY_STATIC(LogStageVerseUI, Log, All);

USVRootLayout* USVUISubsystem::ShowFrontEnd(APlayerController* PlayerController, FName FirstScreen)
{
	if (!RootLayout)
	{
		const TSubclassOf<USVRootLayout> LayoutClass = GetDefault<USVUISettings>()->RootLayoutClass.LoadSynchronous();
		if (!LayoutClass || !PlayerController)
		{
			UE_LOG(LogStageVerseUI, Error, TEXT("ShowFrontEnd: set Root Layout Class in Project Settings > Game > StageVerse UI, and pass the player controller."));
			return nullptr;
		}
		RootLayout = CreateWidget<USVRootLayout>(PlayerController, LayoutClass);
		RootLayout->AddToPlayerScreen(1000);
	}

	if (!FirstScreen.IsNone())
	{
		RootLayout->ClearMenu();
		GoTo(FirstScreen);
	}
	return RootLayout;
}

TSubclassOf<USVScreen> USVUISubsystem::ResolveScreen(FName ScreenId) const
{
	const TSoftClassPtr<USVScreen>* Found = GetDefault<USVUISettings>()->Screens.Find(ScreenId);
	if (!Found)
	{
		UE_LOG(LogStageVerseUI, Warning, TEXT("No widget class for screen '%s' in Project Settings > StageVerse UI > Screens."), *ScreenId.ToString());
		return nullptr;
	}
	return Found->LoadSynchronous();
}

USVScreen* USVUISubsystem::GoTo(FName ScreenId, bool bFromRail)
{
	if (!RootLayout)
	{
		return nullptr;
	}
	const TSubclassOf<USVScreen> ScreenClass = ResolveScreen(ScreenId);
	if (!ScreenClass)
	{
		return nullptr;
	}
	if (bFromRail)
	{
		// Rail items replace the menu level; nothing is ever more than two levels deep.
		RootLayout->ClearMenu();
	}
	const ESVLayer Layer = ScreenId == TEXT("LiveHUD") ? ESVLayer::Hud : ESVLayer::Menu;
	return RootLayout->PushScreen(Layer, ScreenClass);
}

bool USVUISubsystem::Back()
{
	return RootLayout && RootLayout->PopMenu();
}

void USVUISubsystem::OpenShow(const FSVShowListing& Show)
{
	SelectedShow = Show;
	GoTo(TEXT("ShowPage"));
}

void USVUISubsystem::JoinSelectedShow()
{
	// The show level and clock sync come from ShowRuntime; it calls GoTo("LiveHUD") when the clock is locked.
	GoTo(TEXT("DoorsOpen"));
}

void USVUISubsystem::RegisterFXController(ASVShowFXController* Controller)
{
	FXController = Controller;
	if (Controller)
	{
		Controller->SetMode(CurrentMode);
	}
}

void USVUISubsystem::SetLaserMode(ESVLaserMode Mode)
{
	CurrentMode = Mode;
	if (FXController.IsValid())
	{
		FXController->SetMode(Mode);
	}
}

void USVUISubsystem::SetLaserAim(FVector2D NormalizedAim)
{
	if (FXController.IsValid())
	{
		FXController->SetAimInput(NormalizedAim);
	}
}

void USVUISubsystem::FireCO2()
{
	if (FXController.IsValid())
	{
		FXController->FireCO2();
	}
	if (RootLayout)
	{
		RootLayout->PlayCO2Flash();
	}
	OnCO2.Broadcast();
}
