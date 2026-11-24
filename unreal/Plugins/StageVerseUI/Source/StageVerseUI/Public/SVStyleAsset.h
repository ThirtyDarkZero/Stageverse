#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "Fonts/SlateFontInfo.h"
#include "SVStyleAsset.generated.h"

/**
 * The StageVerse brand in one asset ("Loud on the wall, plain on the button").
 * Widgets read colors, fonts and motion timings from here and never hold literal values.
 * Default values match the approved brand sheet (docs/brand/stageverse-front-end.html, Brand sheet tab).
 */
UCLASS(BlueprintType)
class STAGEVERSEUI_API USVStyleAsset : public UPrimaryDataAsset
{
	GENERATED_BODY()

public:
	// ---- Color ----
	/** Ground, panels behind text. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Color")
	FLinearColor Blackout = FLinearColor(FColor(0x08, 0x08, 0x08));

	/** Cards and tiles. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Color")
	FLinearColor Concrete = FLinearColor(FColor(0x14, 0x14, 0x14));

	/** Lines and borders. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Color")
	FLinearColor ConcreteWorn = FLinearColor(FColor(0x2A, 0x2A, 0x2A));

	/** Text, paper posters, selected nav. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Color")
	FLinearColor Wheatpaste = FLinearColor(FColor(0xF1, 0xEE, 0xE8));

	/** Faded print: secondary text. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Color")
	FLinearColor FadedPrint = FLinearColor(FColor(0x9A, 0x97, 0x94));

	/** Primary button and the Live tally. Nothing else is red. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Color")
	FLinearColor RiotRed = FLinearColor(FColor(0xFF, 0x1F, 0x2E));

	/** Light only: focus glow, selection, data. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Color")
	FLinearColor LaserIce = FLinearColor(FColor(0xA8, 0xE8, 0xFF));

	/** Secondary beams. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Color")
	FLinearColor LaserBlue = FLinearColor(FColor(0x2E, 0x6B, 0xFF));

	// ---- Type (fonts are OFL: Archivo, Anton, UnifrakturMaguntia, Space Mono) ----
	/** Archivo Expanded Black. Wordmark only. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Type")
	FSlateFontInfo Wordmark;

	/** Anton. Headlines, show names, buttons. Always uppercase. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Type")
	FSlateFontInfo Headline;

	/** UnifrakturMaguntia. One accent word per screen at most ("Live"). */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Type")
	FSlateFontInfo Accent;

	/** Space Mono. Clocks, BPM, seat numbers, catalog numbers. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Type")
	FSlateFontInfo Data;

	/** Archivo Regular. Reading text. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Type")
	FSlateFontInfo Body;

	// ---- Motion ----
	/** Screen change: 3-frame RGB slice. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Motion", meta = (Units = "s"))
	float GlitchCutSeconds = 0.28f;

	/** White lift on a CO2 blast. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Motion", meta = (Units = "s"))
	float CO2FlashSeconds = 0.5f;

	/** Live HUD fades after this long without input. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Motion", meta = (Units = "s"))
	float HudFadeDelaySeconds = 3.0f;

	/** Beat for the menus when no show is playing. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Motion")
	float MenuBPM = 128.0f;
};
