#pragma once

#include "CoreMinimal.h"
#include "CommonUserWidget.h"
#include "SVTypes.h"
#include "SVRootLayout.generated.h"

class UCommonActivatableWidget;
class UCommonActivatableWidgetStack;
class UMaterialParameterCollection;
class USVScreen;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FSVOnScreenShown, USVScreen*, Screen);

/**
 * The one widget that owns every screen. WBP_RootLayout derives from this and must contain
 * three CommonActivatableWidgetStacks named MenuStack, HudStack and ModalStack (bottom to top).
 * The arena level renders behind it, so leave the root background transparent.
 *
 * It also drives the street FX: a glitch cut on every screen change and the CO2 flash,
 * written to MPC_StageVerseFX for PP_StreetGlitch to read.
 */
UCLASS(Abstract)
class STAGEVERSEUI_API USVRootLayout : public UCommonUserWidget
{
	GENERATED_BODY()

public:
	/** Push a screen class onto a layer. Returns the new screen, or null if the class is empty. */
	UFUNCTION(BlueprintCallable, Category = "StageVerse")
	USVScreen* PushScreen(ESVLayer Layer, TSubclassOf<USVScreen> ScreenClass);

	/** Close the top screen of the menu stack (what B and Esc do). Returns false at the bottom of the stack. */
	UFUNCTION(BlueprintCallable, Category = "StageVerse")
	bool PopMenu();

	/** Clear the menu stack, e.g. when a rail item is chosen, so Back never goes sideways. */
	UFUNCTION(BlueprintCallable, Category = "StageVerse")
	void ClearMenu();

	UFUNCTION(BlueprintCallable, Category = "StageVerse")
	void PlayGlitchCut();

	UFUNCTION(BlueprintCallable, Category = "StageVerse")
	void PlayCO2Flash();

	UFUNCTION(BlueprintPure, Category = "StageVerse")
	USVScreen* GetTopMenuScreen() const;

	/** Fires after each screen becomes the visible one, after the glitch cut starts. */
	UPROPERTY(BlueprintAssignable, Category = "StageVerse")
	FSVOnScreenShown OnScreenShown;

protected:
	UPROPERTY(BlueprintReadOnly, Category = "StageVerse", meta = (BindWidget))
	TObjectPtr<UCommonActivatableWidgetStack> MenuStack;

	UPROPERTY(BlueprintReadOnly, Category = "StageVerse", meta = (BindWidget))
	TObjectPtr<UCommonActivatableWidgetStack> HudStack;

	UPROPERTY(BlueprintReadOnly, Category = "StageVerse", meta = (BindWidget))
	TObjectPtr<UCommonActivatableWidgetStack> ModalStack;

	/** The rail, if the blueprint has one; hidden on screens with bShowsRail off. */
	UPROPERTY(BlueprintReadOnly, Category = "StageVerse", meta = (BindWidgetOptional))
	TObjectPtr<UWidget> Rail;

	virtual void NativeOnInitialized() override;
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;

private:
	void HandleDisplayedWidgetChanged(UCommonActivatableWidget* Widget);
	void WriteFX(FName Param, float Value) const;
	bool ShouldReduceMotion() const;

	UPROPERTY(Transient)
	TObjectPtr<UMaterialParameterCollection> FXCollection;

	float GlitchRemaining = 0.f;
	float GlitchDuration = 0.28f;
	float FlashRemaining = 0.f;
	float FlashDuration = 0.5f;
};
