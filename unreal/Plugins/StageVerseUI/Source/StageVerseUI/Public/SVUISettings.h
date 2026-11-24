#pragma once

#include "CoreMinimal.h"
#include "Engine/DeveloperSettings.h"
#include "SVUISettings.generated.h"

class USVStyleAsset;
class USVRootLayout;
class USVScreen;
class UMaterialParameterCollection;

/** Project Settings > Game > StageVerse UI. */
UCLASS(Config = Game, DefaultConfig, meta = (DisplayName = "StageVerse UI"))
class STAGEVERSEUI_API USVUISettings : public UDeveloperSettings
{
	GENERATED_BODY()

public:
	virtual FName GetCategoryName() const override { return TEXT("Game"); }

	/** The brand asset (DA_StageVerseStyle). */
	UPROPERTY(Config, EditAnywhere, Category = "Brand")
	TSoftObjectPtr<USVStyleAsset> Style;

	/** WBP_RootLayout: must contain stacks named MenuStack, HudStack and ModalStack. */
	UPROPERTY(Config, EditAnywhere, Category = "Screens")
	TSoftClassPtr<USVRootLayout> RootLayoutClass;

	/**
	 * Screen id to widget class. Ids used by the router: Title, Tonight, Shows, ShowPage, Tickets,
	 * Studio, BuildShow, Building, ShowProducer, DoorsOpen, LiveHUD.
	 */
	UPROPERTY(Config, EditAnywhere, Category = "Screens")
	TMap<FName, TSoftClassPtr<USVScreen>> Screens;

	/** MPC_StageVerseFX: scalars Glitch, CO2Flash, Beat read by PP_StreetGlitch. */
	UPROPERTY(Config, EditAnywhere, Category = "FX")
	TSoftObjectPtr<UMaterialParameterCollection> FXCollection;

	/** Turns off strobe, glitch cuts and the laser beat pulse. Players change it in Settings. */
	UPROPERTY(Config, EditAnywhere, Category = "Accessibility")
	bool bReduceMotion = false;
};
