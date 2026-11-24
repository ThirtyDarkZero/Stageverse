#include "SVScreen.h"
#include "SVUISubsystem.h"
#include "SVUILibrary.h"
#include "Engine/LocalPlayer.h"

USVUISubsystem* USVScreen::GetUI() const
{
	const ULocalPlayer* LocalPlayer = GetOwningLocalPlayer();
	return LocalPlayer ? LocalPlayer->GetSubsystem<USVUISubsystem>() : nullptr;
}

const USVStyleAsset* USVScreen::GetStyle() const
{
	return USVUILibrary::GetStageVerseStyle();
}

UWidget* USVScreen::NativeGetDesiredFocusTarget() const
{
	if (DefaultFocus)
	{
		return DefaultFocus;
	}
	return Super::NativeGetDesiredFocusTarget();
}
