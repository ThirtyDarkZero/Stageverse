#pragma once

#include "CoreMinimal.h"
#include "CommonActivatableWidget.h"
#include "SVTypes.h"
#include "SVScreen.generated.h"

class USVUISubsystem;
class USVStyleAsset;

/**
 * Base for every StageVerse screen. C++ holds the logic, a widget blueprint holds the layout.
 * Rule from the brand: the primary action is always the default focus, so a controller player only presses A.
 */
UCLASS(Abstract, Blueprintable)
class STAGEVERSEUI_API USVScreen : public UCommonActivatableWidget
{
	GENERATED_BODY()

public:
	/** Router id (Title, Tonight, ShowPage...). Must match the key in Project Settings > StageVerse UI > Screens. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "StageVerse")
	FName ScreenId;

	/** How hard the lasers run while this screen is on top. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "StageVerse")
	ESVLaserMode LaserMode = ESVLaserMode::Menu;

	/** Shows the left rail (Tonight, Shows, My tickets, Studio). Off for Title, DoorsOpen and the Live HUD. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "StageVerse")
	bool bShowsRail = true;

	UFUNCTION(BlueprintPure, Category = "StageVerse")
	USVUISubsystem* GetUI() const;

	UFUNCTION(BlueprintPure, Category = "StageVerse")
	const USVStyleAsset* GetStyle() const;

protected:
	/** Name a widget "DefaultFocus" in the blueprint (usually the primary button) and it gets focus on activation. */
	UPROPERTY(BlueprintReadOnly, Category = "StageVerse", meta = (BindWidgetOptional))
	TObjectPtr<UWidget> DefaultFocus;

	virtual UWidget* NativeGetDesiredFocusTarget() const override;
};
