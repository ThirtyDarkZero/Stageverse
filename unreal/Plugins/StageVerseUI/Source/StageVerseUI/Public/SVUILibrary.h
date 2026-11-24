#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "SVTypes.h"
#include "SVUILibrary.generated.h"

class USVStyleAsset;

UCLASS()
class STAGEVERSEUI_API USVUILibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	/** The brand asset from Project Settings > StageVerse UI. */
	UFUNCTION(BlueprintPure, Category = "StageVerse")
	static const USVStyleAsset* GetStageVerseStyle();

	/** Parse a JSON array of shows (the backend's /shows response body). */
	UFUNCTION(BlueprintCallable, Category = "StageVerse")
	static bool ParseShowsJson(const FString& Json, TArray<FSVShowListing>& OutShows);

	/** Example shows from Resources/SampleShows.json, used until the backend is hooked up. */
	UFUNCTION(BlueprintCallable, Category = "StageVerse")
	static bool LoadSampleShows(TArray<FSVShowListing>& OutShows);

	/** Background, type and accent colors for a poster paper. */
	UFUNCTION(BlueprintPure, Category = "StageVerse")
	static void GetPosterColors(ESVPosterPaper Paper, FLinearColor& Background, FLinearColor& Type, FLinearColor& Accent);

	/** "14,212 watching" */
	UFUNCTION(BlueprintPure, Category = "StageVerse")
	static FText FormatWatchers(int32 Watchers);

	/** "SAT 28 NOV · 21:00" in the player's local time; "LIVE NOW" or "REPLAY · 21 NOV" when those apply. */
	UFUNCTION(BlueprintPure, Category = "StageVerse")
	static FText FormatShowDate(const FSVShowListing& Show);

	/** Tonight's hero: the first live show, else the next upcoming one. */
	UFUNCTION(BlueprintPure, Category = "StageVerse")
	static bool PickTonightHero(const TArray<FSVShowListing>& Shows, FSVShowListing& OutHero);
};
