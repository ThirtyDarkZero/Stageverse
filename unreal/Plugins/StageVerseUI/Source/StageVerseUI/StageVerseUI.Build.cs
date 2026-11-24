using UnrealBuildTool;

public class StageVerseUI : ModuleRules
{
	public StageVerseUI(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDependencyModuleNames.AddRange(new string[]
		{
			"Core",
			"CoreUObject",
			"Engine",
			"UMG",
			"SlateCore",
			"CommonUI",
			"CommonInput",
			"Niagara",
			"DeveloperSettings"
		});

		PrivateDependencyModuleNames.AddRange(new string[]
		{
			"Slate",
			"Json",
			"JsonUtilities",
			"Projects"
		});
	}
}
