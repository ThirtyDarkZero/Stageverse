#pragma once

#include "CoreMinimal.h"
#include "Subsystems/LocalPlayerSubsystem.h"
#include "SVTypes.h"
#include "SVUISubsystem.generated.h"

class APlayerController;
class ASVShowFXController;
class USVRootLayout;
class USVScreen;

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FSVOnCO2);

/**
 * The front-end router for one local player.
 * Call ShowFrontEnd from the front-end player controller's BeginPlay; it builds the root layout,
 * opens the Title screen and links up the laser rig in the level.
 */
UCLASS()
class STAGEVERSEUI_API USVUISubsystem : public ULocalPlayerSubsystem
{
	GENERATED_BODY()

public:
	/** Create the root layout (once) and open a first screen, Title by default. */
	UFUNCTION(BlueprintCallable, Category = "StageVerse")
	USVRootLayout* ShowFrontEnd(APlayerController* PlayerController, FName FirstScreen = "Title");

	/** Open a screen by id on top of the current one. Rail items pass bFromRail so Back returns to the rail level. */
	UFUNCTION(BlueprintCallable, Category = "StageVerse")
	USVScreen* GoTo(FName ScreenId, bool bFromRail = false);

	/** B / Esc. Returns false when there is nothing to go back to. */
	UFUNCTION(BlueprintCallable, Category = "StageVerse")
	bool Back();

	/** Remember the show and open its show page. */
	UFUNCTION(BlueprintCallable, Category = "StageVerse")
	void OpenShow(const FSVShowListing& Show);

	/** Join the selected show: DoorsOpen now, the Live HUD once the show level reports ready. */
	UFUNCTION(BlueprintCallable, Category = "StageVerse")
	void JoinSelectedShow();

	UFUNCTION(BlueprintPure, Category = "StageVerse")
	FSVShowListing GetSelectedShow() const { return SelectedShow; }

	UFUNCTION(BlueprintPure, Category = "StageVerse")
	USVRootLayout* GetRootLayout() const { return RootLayout; }

	// ---- Lasers and CO2 ----
	void RegisterFXController(ASVShowFXController* Controller);

	UFUNCTION(BlueprintCallable, Category = "StageVerse|FX")
	void SetLaserMode(ESVLaserMode Mode);

	/** Normalized aim, 0..1 on both axes (cursor position or right stick mapped to 0..1). */
	UFUNCTION(BlueprintCallable, Category = "StageVerse|FX")
	void SetLaserAim(FVector2D NormalizedAim);

	/** Fire the CO2 jets and flash the UI. Bound to A on empty fog, and the CO2 button in a show. */
	UFUNCTION(BlueprintCallable, Category = "StageVerse|FX")
	void FireCO2();

	UPROPERTY(BlueprintAssignable, Category = "StageVerse|FX")
	FSVOnCO2 OnCO2;

private:
	TSubclassOf<USVScreen> ResolveScreen(FName ScreenId) const;

	UPROPERTY(Transient)
	TObjectPtr<USVRootLayout> RootLayout;

	TWeakObjectPtr<ASVShowFXController> FXController;

	FSVShowListing SelectedShow;
	ESVLaserMode CurrentMode = ESVLaserMode::Title;
};
