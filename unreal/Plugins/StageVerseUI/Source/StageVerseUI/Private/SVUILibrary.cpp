#include "SVUILibrary.h"
#include "SVStyleAsset.h"
#include "SVUISettings.h"
#include "JsonObjectConverter.h"
#include "Interfaces/IPluginManager.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"

const USVStyleAsset* USVUILibrary::GetStageVerseStyle()
{
	return GetDefault<USVUISettings>()->Style.LoadSynchronous();
}

bool USVUILibrary::ParseShowsJson(const FString& Json, TArray<FSVShowListing>& OutShows)
{
	OutShows.Reset();
	return FJsonObjectConverter::JsonArrayStringToUStruct(Json, &OutShows, 0, 0);
}

bool USVUILibrary::LoadSampleShows(TArray<FSVShowListing>& OutShows)
{
	const TSharedPtr<IPlugin> Plugin = IPluginManager::Get().FindPlugin(TEXT("StageVerseUI"));
	if (!Plugin.IsValid())
	{
		return false;
	}
	FString Json;
	const FString Path = FPaths::Combine(Plugin->GetBaseDir(), TEXT("Resources"), TEXT("SampleShows.json"));
	return FFileHelper::LoadFileToString(Json, *Path) && ParseShowsJson(Json, OutShows);
}

void USVUILibrary::GetPosterColors(ESVPosterPaper Paper, FLinearColor& Background, FLinearColor& Type, FLinearColor& Accent)
{
	const USVStyleAsset* Style = GetStageVerseStyle();
	const USVStyleAsset* S = Style ? Style : GetDefault<USVStyleAsset>();
	switch (Paper)
	{
	case ESVPosterPaper::Blackout:
		Background = S->Blackout; Type = S->Wheatpaste; Accent = S->RiotRed;
		break;
	case ESVPosterPaper::Wheatpaste:
		Background = S->Wheatpaste; Type = S->Blackout; Accent = S->RiotRed;
		break;
	case ESVPosterPaper::RiotRed:
	default:
		Background = S->RiotRed; Type = S->Blackout; Accent = S->Wheatpaste;
		break;
	}
}

FText USVUILibrary::FormatWatchers(int32 Watchers)
{
	return FText::Format(NSLOCTEXT("StageVerse", "Watching", "{0} watching"), FText::AsNumber(Watchers));
}

FText USVUILibrary::FormatShowDate(const FSVShowListing& Show)
{
	if (Show.bLive)
	{
		return NSLOCTEXT("StageVerse", "LiveNow", "LIVE NOW");
	}
	FDateTime Utc;
	if (!FDateTime::ParseIso8601(*Show.StartsAt, Utc))
	{
		return FText::FromString(Show.StartsAt);
	}
	const FDateTime Local = Utc + (FDateTime::Now() - FDateTime::UtcNow());
	static const TCHAR* Days[] = { TEXT("MON"), TEXT("TUE"), TEXT("WED"), TEXT("THU"), TEXT("FRI"), TEXT("SAT"), TEXT("SUN") };
	static const TCHAR* Months[] = { TEXT("JAN"), TEXT("FEB"), TEXT("MAR"), TEXT("APR"), TEXT("MAY"), TEXT("JUN"), TEXT("JUL"), TEXT("AUG"), TEXT("SEP"), TEXT("OCT"), TEXT("NOV"), TEXT("DEC") };
	const FString Month = Months[Local.GetMonth() - 1];
	if (Show.bReplay)
	{
		return FText::FromString(FString::Printf(TEXT("REPLAY · %02d %s"), Local.GetDay(), *Month));
	}
	return FText::FromString(FString::Printf(TEXT("%s %02d %s · %02d:%02d"),
		Days[static_cast<int32>(Local.GetDayOfWeek())], Local.GetDay(), *Month, Local.GetHour(), Local.GetMinute()));
}

bool USVUILibrary::PickTonightHero(const TArray<FSVShowListing>& Shows, FSVShowListing& OutHero)
{
	for (const FSVShowListing& Show : Shows)
	{
		if (Show.bLive)
		{
			OutHero = Show;
			return true;
		}
	}
	const FDateTime Now = FDateTime::UtcNow();
	const FSVShowListing* Next = nullptr;
	FDateTime NextTime = FDateTime::MaxValue();
	for (const FSVShowListing& Show : Shows)
	{
		FDateTime When;
		if (!Show.bReplay && FDateTime::ParseIso8601(*Show.StartsAt, When) && When > Now && When < NextTime)
		{
			Next = &Show;
			NextTime = When;
		}
	}
	if (Next)
	{
		OutHero = *Next;
		return true;
	}
	return false;
}
