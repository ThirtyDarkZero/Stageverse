#pragma once

#include "CoreMinimal.h"
#include "SVTypes.generated.h"

/** How hard the laser rig runs behind the current screen. */
UENUM(BlueprintType)
enum class ESVLaserMode : uint8
{
	Title,      // full rig, the title screen is the show
	Menu,       // low level behind menus, panels stay readable
	DoorsOpen,  // white-ish wash while the show loads
	Live        // full rig, driven by the show's cues
};

UENUM(BlueprintType)
enum class ESVVenueTier : uint8
{
	Club,
	Theater,
	Arena,
	Stadium
};

/** The three street-poster papers an artist can pick. */
UENUM(BlueprintType)
enum class ESVPosterPaper : uint8
{
	RiotRed,
	Blackout,
	Wheatpaste
};

/** Which stack a screen is pushed onto in the root layout. */
UENUM(BlueprintType)
enum class ESVLayer : uint8
{
	Menu,
	Hud,
	Modal
};

/** One show as the front end needs it. Filled from the backend's /shows, or from Resources/SampleShows.json. */
USTRUCT(BlueprintType)
struct STAGEVERSEUI_API FSVShowListing
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Show") FString Id;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Show") FString Name;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Show") FString Artist;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Show") ESVVenueTier Tier = ESVVenueTier::Arena;
	/** ISO 8601, UTC. Shown in the player's time zone. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Show") FString StartsAt;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Show") bool bLive = false;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Show") bool bReplay = false;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Show") int32 Watchers = 0;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Show") int32 Seats = 0;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Show") int32 Songs = 0;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Show") int32 LengthMinutes = 0;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Show") float BPM = 128.f;
	/** Catalog number printed on the poster, e.g. SV-001. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Poster") FString Catalog;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Poster") ESVPosterPaper Paper = ESVPosterPaper::RiotRed;
	/** The one blackletter word on the poster. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Poster") FString AccentWord;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Show") TArray<FString> Setlist;
};
