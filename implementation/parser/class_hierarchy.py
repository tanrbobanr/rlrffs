from __future__ import annotations
from typing import *

from .enums import SpawnTrajectory, AttributeType


_ParentMap: TypeAlias = dict[str, "_ParentMap | None"]
_T = TypeVar("_T")
_MISSING = object()


class ClassInfo(NamedTuple):
    name: str
    parent: "ClassInfo" | None
    spawn_trajectory: SpawnTrajectory
    attribute_type: AttributeType | None


def _build_class_hierarchy(
    spawns: dict[str, SpawnTrajectory],
    attributes: dict[str, dict[str, AttributeType]],
    parent_map: _ParentMap, parent: ClassInfo | None = None,
    class_hierarchy: dict[str, ClassInfo] = None
) -> dict[str, ClassInfo]:
    if class_hierarchy is None:
        class_hierarchy = dict()

    for pname, children in parent_map.items():
        # create parent and add to class hierarchy
        new_parent = ClassInfo(
            name=pname,
            parent=parent,
            spawn_trajectory=(
                spawns.get(pname)
                or (parent and parent.spawn_trajectory)
                or SpawnTrajectory.none
            ),
            attribute_type=None
        )

        class_hierarchy[pname.casefold()] = new_parent

        # add attributes
        for aname, atype in attributes.get(pname, {}).items():
            full_aname = f"{pname}:{aname}"
            class_hierarchy[full_aname.casefold()] = ClassInfo(
                name=full_aname,
                parent=new_parent,
                spawn_trajectory=new_parent.spawn_trajectory,
                attribute_type=atype
            )

        if children:
            _build_class_hierarchy(
                spawns=spawns,
                attributes=attributes,
                parent_map=children,
                parent=new_parent,
                class_hierarchy=class_hierarchy
            )

    return class_hierarchy


class ClassHierarchy(dict[str, ClassInfo]):
    def __getitem__(self, key: str) -> ClassInfo:
        try:
            return super().__getitem__(key.casefold())
        except KeyError as exc:
            raise KeyError(key) from exc

    @overload
    def get(self, key: str, /) -> ClassInfo: ...
    @overload
    def get(self, key: str, default: _T) -> ClassInfo | _T: ...
    def get(
        self, key: str, default: _T = _MISSING
    ) -> ClassInfo | _T:
        if default is _MISSING:
            return self[key]
        return super().get(key.casefold(), default)

    @classmethod
    def build(
        cls, spawns: dict[str, SpawnTrajectory],
        attributes: dict[str, dict[str, AttributeType]],
        parent_map: _ParentMap
    ) -> Self:
        return cls(_build_class_hierarchy(spawns, attributes, parent_map))


def _gria(s: str, is_gameinfo: bool = True) -> str:
    """Build a GameReplicationInfoArchetype object"""
    gi = f"GameInfo_{s}"
    center = "GameInfo" if is_gameinfo else s
    return f"{gi}.{center}.{gi}:GameReplicationInfoArchetype"


_SPAWNS = {
    "Engine.Actor": SpawnTrajectory.loc,
    "Engine.ZoneInfo": SpawnTrajectory.none,
    "TAGame.BreakOutActor_Platform_TA": SpawnTrajectory.none,
    "TAGame.CrowdActor_TA": SpawnTrajectory.none,
    "TAGame.CrowdManager_TA": SpawnTrajectory.none,
    "TAGame.HauntedBallTrapTrigger_TA": SpawnTrajectory.none,
    "TAGame.InMapScoreboard_TA": SpawnTrajectory.none,
    "TAGame.PlayerStart_Platform_TA": SpawnTrajectory.none,
    "TAGame.RBActor_TA": SpawnTrajectory.loc_rot,
    "TAGame.VehiclePickup_Boost_TA": SpawnTrajectory.none,
    "TAGame.KeepUpIndicator_TA": SpawnTrajectory.loc_rot,
}

_ATTRIBUTES = {
    "Engine.Actor": {
        "bBlockActors": AttributeType.boolean,
        "bCollideActors": AttributeType.boolean,
        "bCollideWorld": AttributeType.boolean,
        # "bHardAttach": AttributeType.boolean,
        "bHidden": AttributeType.boolean,
        "bNetOwner": AttributeType.boolean,
        "bTearOff": AttributeType.boolean,
        "DrawScale": AttributeType.float_32,
        # "Instigator": AttributeType.pointer,
        # "Owner": AttributeType.pointer,
        # "Physics": AttributeType.uint_8,
        # "RelativeRotation": AttributeType.rotation,
        "RemoteRole": AttributeType.uint_11,
        # "ReplicatedCollisionType": AttributeType.uint_8,
        "Role": AttributeType.uint_11,
        "Rotation": AttributeType.rotation,
    },
    "Engine.GameReplicationInfo": {
        # "bMatchHasBegun": AttributeType.boolean,
        "bMatchIsOver": AttributeType.boolean,
        # "bStopCountDown": AttributeType.boolean,
        # "ElapsedTime": AttributeType.int_32,
        "GameClass": AttributeType.pointer,
        # "GoalScore": AttributeType.int_32,
        # "RemainingMinute": AttributeType.int_32,
        # "RemainingTime": AttributeType.int_32,
        "ServerName": AttributeType.string,
        # "TimeLimit": AttributeType.int_32,
        # "Winner": AttributeType.pointer,
    },
    "Engine.Pawn": {
        # "AccelRate": AttributeType.float_32,
        # "AirControl": AttributeType.float_32,
        # "AirSpeed": AttributeType.float_32,
        # "bCanSwatTurn": AttributeType.boolean,
        "bFastAttachedMove": AttributeType.boolean,
        "bIsCrouched": AttributeType.boolean,
        # "bIsWalking": AttributeType.boolean,
        # "bRootMotionFromInterpCurve": AttributeType.boolean,
        # "bSimulateGravity": AttributeType.boolean,
        "bUsedByMatinee": AttributeType.boolean,
        # "Controller": AttributeType.pointer,
        # "GroundSpeed": AttributeType.float_32,
        "HealthMax": AttributeType.int_32,
        # "JumpZ": AttributeType.float_32,
        "PlayerReplicationInfo": AttributeType.pointer,
        "RemoteViewPitch": AttributeType.uint_8,
        # "RootMotionInterpCurrentTime": AttributeType.float_32,
        # "RootMotionInterpRate": AttributeType.float_32,
    },
    "Engine.PlayerReplicationInfo": {
        "bAdmin": AttributeType.boolean,
        "bBot": AttributeType.boolean,
        # "bFromPreviousLevel": AttributeType.boolean,
        # "bIsInactive": AttributeType.boolean,
        "bIsSpectator": AttributeType.boolean,
        # "bOnlySpectator": AttributeType.boolean,
        # "bOutOfLives": AttributeType.boolean,
        "bReadyToPlay": AttributeType.boolean,
        "bTimedOut": AttributeType.boolean,
        "bWaitingPlayer": AttributeType.boolean,
        # "Deaths": AttributeType.int_32,
        "Ping": AttributeType.uint_8,
        "PlayerID": AttributeType.int_32,
        "PlayerName": AttributeType.string,
        "RemoteUserData": AttributeType.string,
        "Score": AttributeType.int_32,
        "Team": AttributeType.pointer,
        "UniqueId": AttributeType.unique_id,
    },
    "Engine.ReplicatedActor_ORS": {
        "ReplicatedOwner": AttributeType.pointer,
    },
    "Engine.TeamInfo": {
        "Score": AttributeType.int_32,
        # "TeamIndex": AttributeType.int_32,
        # "TeamName": AttributeType.string,
    },
    "ProjectX.GRI_X": {
        # "bGameEnded": AttributeType.boolean,
        "bGameStarted": AttributeType.boolean,
        "GameServerID": AttributeType.game_server,
        "MatchGuid": AttributeType.string,
        "ReplicatedGameMutatorIndex": AttributeType.int_32,
        "ReplicatedGamePlaylist": AttributeType.int_32,
        "ReplicatedServerRegion": AttributeType.string,
        "Reservations": AttributeType.reservation,
    },
    "TAGame.Ball_Breakout_TA": {
        "AppliedDamage": AttributeType.applied_damage,
        "DamageIndex": AttributeType.int_32,
        "LastTeamTouch": AttributeType.uint_8,
    },
    "TAGame.Ball_Fire_TA": {
        "TeamNumChangeTimestamp": AttributeType.float_32,
    },
    "TAGame.Ball_God_TA": {
        "TargetSpeed": AttributeType.float_32,
    },
    "TAGame.Ball_Haunted_TA": {
        "bIsBallBeamed": AttributeType.boolean,
        "DeactivatedGoalIndex": AttributeType.uint_8,
        "LastTeamTouch": AttributeType.uint_8,
        "ReplicatedBeamBrokenValue": AttributeType.uint_8,
        "TotalActiveBeams": AttributeType.uint_8,
    },
    "TAGame.Ball_TA": {
        "AirResistance": AttributeType.vector_3f,
        "AdditionalCarGroundBounceScaleXY": AttributeType.float_32,
        # "AdditionalCarGroundBounceScaleZ": AttributeType.float_32, !!!
        "BallHitSpinScale": AttributeType.float_32,
        # "bEndOfGameHidden": AttributeType.boolean,
        "bPossessionEnabled": AttributeType.boolean,
        "bWarnBallReset": AttributeType.boolean,
        "GameBallIndex": AttributeType.int_32,
        "GameEvent": AttributeType.pointer,
        "HitTeamNum": AttributeType.uint_8,
        "MagnusMinSpeed": AttributeType.float_32,
        "ReplicatedAddedCarBounceScale": AttributeType.float_32,
        "ReplicatedBallGravityScale": AttributeType.float_32,
        "ReplicatedBallMaxLinearSpeedScale": AttributeType.float_32,
        # "ReplicatedBallMesh": AttributeType.pointer,
        "ReplicatedBallScale": AttributeType.float_32,
        "ReplicatedExplosionData": AttributeType.explosion,
        "ReplicatedExplosionDataExtended": AttributeType.explosion_extended,
        "ReplicatedPhysMatOverride": AttributeType.pointer,
        "ReplicatedWorldBounceScale": AttributeType.float_32,
    },
    "TAGame.BreakOutActor_Platform_TA": {
        # "bLockedDamageState": AttributeType.boolean,
        "DamageState": AttributeType.damage_state,
        # "DefaultDamageState": AttributeType.uint_8,
    },
    "TAGame.CameraSettingsActor_TA": {
        # "bHoldMouseCamera": AttributeType.boolean,
        "bMouseCameraToggleEnabled": AttributeType.boolean,
        # "bResetCamera": AttributeType.boolean,
        "bUsingBehindView": AttributeType.boolean,
        # "bUsingFreecam": AttributeType.boolean,
        "bUsingSecondaryCamera": AttributeType.boolean,
        "bUsingSwivel": AttributeType.boolean,
        "CameraPitch": AttributeType.uint_8,
        "CameraYaw": AttributeType.uint_8,
        "PRI": AttributeType.pointer,
        "ProfileSettings": AttributeType.camera_settings,
    },
    "TAGame.Cannon_TA": {
        "FireCount": AttributeType.uint_8,
        "Pitch": AttributeType.float_32,
    },
    "TAGame.Car_KnockOut_TA": {
        "ReplicatedImpulse": AttributeType.impulse,
        "ReplicatedStateChanged": AttributeType.uint_8,
        "ReplicatedStateName": AttributeType.int_32,
        "UsedAttackComponent": AttributeType.pointer,
    },
    "TAGame.Car_TA": {
        "AddedBallForceMultiplier": AttributeType.float_32,
        "AddedCarForceMultiplier": AttributeType.float_32,
        "AttachedPickup": AttributeType.pointer,
        # "bOverrideBoostOn": AttributeType.boolean,
        # "bOverrideHandbrakeOn": AttributeType.boolean,
        "bUnlimitedJumps": AttributeType.boolean,
        "bUnlimitedTimeForDodge": AttributeType.boolean,
        "ClubColors": AttributeType.club_colors,
        "DodgesRefreshedCounter": AttributeType.int_32,
        # "MaxNumJumps": AttributeType.int_32,
        # "MaxTimeForDodge": AttributeType.float_32,
        # "PostMatchAnim": AttributeType.int_32,
        "ReplicatedCarMaxLinearSpeedScale": AttributeType.float_32,
        "ReplicatedCarScale": AttributeType.float_32,
        "ReplicatedDemolish_CustomFX": AttributeType.demolish_fx,
        "ReplicatedDemolish": AttributeType.demolish,
        "ReplicatedDemolishExtended": AttributeType.demolish_extended,
        "ReplicatedDemolishGoalExplosion": AttributeType.demolish_fx,
        "RumblePickups": AttributeType.pointer,
        "TeamPaint": AttributeType.team_paint,
    },
    "TAGame.CarComponent_AirActivate_TA": {
        "AirActivateCount": AttributeType.int_32,
    },
    "TAGame.CarComponent_Boost_TA": {
        "bNoBoost": AttributeType.boolean,
        "BoostModifier": AttributeType.float_32,
        "BoostRestriction": AttributeType.uint_8,
        "bRechargeGroundOnly": AttributeType.boolean,
        "bUnlimitedBoost": AttributeType.boolean,
        # "CurrentBoostAmount": AttributeType.float_32,
        "RechargeDelay": AttributeType.float_32,
        "RechargeRate": AttributeType.float_32,
        "ReplicatedBoost": AttributeType.replicated_boost,
        "ReplicatedBoostAmount": AttributeType.uint_8,
        # "StartBoostAmount": AttributeType.float_32,
        "UnlimitedBoostRefCount": AttributeType.int_32,
    },
    "TAGame.CarComponent_Dodge_KO_TA": {
        "DodgeRotationCompressed": AttributeType.int_32,
    },
    "TAGame.CarComponent_Dodge_TA": {
        "DodgeImpulse": AttributeType.vector_3f,
        "DodgeTorque": AttributeType.vector_3f,
    },
    "TAGame.CarComponent_DoubleJump_TA": {
        "DoubleJumpImpulse": AttributeType.vector_3f,
    },
    "TAGame.CarComponent_FlipCar_TA": {
        "bFlipRight": AttributeType.boolean,
        "FlipCarTime": AttributeType.float_32,
    },
    "TAGame.CarComponent_TA": {
        "ReplicatedActive": AttributeType.uint_8,
        "ReplicatedActivityTime": AttributeType.float_32,
        "Vehicle": AttributeType.pointer,
    },
    "TAGame.CarComponent_Torque_TA": {
        "ReplicatedTorqueInput": AttributeType.int_32,
        "TorqueScale": AttributeType.float_32,
    },
    "TAGame.CrowdActor_TA": {
        "GameEvent": AttributeType.pointer,
        "ModifiedNoise": AttributeType.float_32,
        "ReplicatedCountDownNumber": AttributeType.int_32,
        "ReplicatedOneShotSound": AttributeType.pointer,
        "ReplicatedRoundCountDownNumber": AttributeType.int_32,
    },
    "TAGame.CrowdManager_TA": {
        "GameEvent": AttributeType.pointer,
        "ReplicatedGlobalOneShotSound": AttributeType.pointer,
    },
    "TAGame.GameEvent_Soccar_TA": {
        # "bAllowHonorDuels": AttributeType.boolean, !!!
        # "bAntiCheatTerminated": AttributeType.boolean,
        "bBallHasBeenHit": AttributeType.boolean,
        # "bCanDropOnlineRewards": AttributeType.boolean,
        "bClubMatch": AttributeType.boolean,
        "bDisableCrowdSound": AttributeType.boolean,
        "bFullClubMatch": AttributeType.boolean,
        "bFullMatchWinnerDecided": AttributeType.boolean,
        "bGoalsEnabled": AttributeType.boolean,
        "bMatchCreatorAdminEnabled": AttributeType.boolean,
        "bMatchEnded": AttributeType.boolean,
        "bNoContest": AttributeType.boolean,
        "bOverTime": AttributeType.boolean,
        "bReadyToStartGame": AttributeType.boolean,
        "bShouldSpawnGoalIndicators": AttributeType.boolean,
        # "bShowIntroScene": AttributeType.boolean, !!!
        # "bThistleMatch": AttributeType.boolean,
        "bUnlimitedTime": AttributeType.boolean,
        "GameTime": AttributeType.int_32,
        "GameWinner": AttributeType.pointer,
        "MatchWinner": AttributeType.pointer,
        "MaxScore": AttributeType.int_32,
        "MVP": AttributeType.pointer,
        # "ReplayDirector": AttributeType.pointer,
        "ReplicatedMusicStinger": AttributeType.music_stinger,
        "ReplicatedScoredOnTeam": AttributeType.uint_8,
        "ReplicatedServerPerformanceState": AttributeType.uint_8,
        "ReplicatedStatEvent": AttributeType.pointer,
        "RoundNum": AttributeType.int_32,
        "SecondsRemaining": AttributeType.int_32,
        "SeriesLength": AttributeType.int_32,
        "SubRulesArchetype": AttributeType.pointer,
        # "TieBreakDecision": AttributeType.uint_8,
        # "TotalGameBalls": AttributeType.int_32, !!!
        # "WaitTimeRemaining": AttributeType.int_32,
    },
    "TAGame.GameEvent_SoccarPrivate_TA": {
        # "GameOwner": AttributeType.pointer,
        "MatchSettings": AttributeType.match_settings,
    },
    "TAGame.GameEvent_TA": {
        # "ActivatorCar": AttributeType.pointer,
        # "bAllowQueueSaveReplay": AttributeType.boolean,
        "bAllowReadyUp": AttributeType.boolean,
        "bAlwaysShowMatchTypeLabel": AttributeType.boolean,
        "bCanVoteToForfeit": AttributeType.boolean,
        "bHasLeaveMatchPenalty": AttributeType.boolean,
        "bIsBotMatch": AttributeType.boolean,
        "BotSkill": AttributeType.int_32,
        # "DemoFXOverride": AttributeType.pointer,
        "GameMode": AttributeType.game_mode,
        # "GameOwner": AttributeType.pointer,
        # "MatchSettings": AttributeType.match_settings,
        "MatchStartEpoch": AttributeType.int_64,
        # "MatchTotalSecondsPlayed": AttributeType.int_32,
        "MatchTypeClass": AttributeType.pointer,
        "ReplicatedGameStateTimeRemaining": AttributeType.int_32,
        "ReplicatedRoundCountDownNumber": AttributeType.int_32,
        "ReplicatedStateIndex": AttributeType.uint_8,
        "ReplicatedStateName": AttributeType.int_32,
        "RichPresenceString": AttributeType.string,
    },
    "TAGame.GameEvent_Team_TA": {
        # "bDisableMutingOtherTeam": AttributeType.boolean,
        "bDisableQuickChat": AttributeType.boolean,
        "bForfeit": AttributeType.boolean,
        "MaxTeamSize": AttributeType.int_32,
    },
    "TAGame.GRI_TA": {
        "bAllowTargetFind": AttributeType.boolean,
        "NewDedicatedServerIP": AttributeType.string,
    },
    "TAGame.MaxTimeWarningData_TA": {
        "EndGameEpochTime": AttributeType.int_64,
        "EndGameWarningEpochTime": AttributeType.int_64,
    },
    "TAGame.PlayerStart_Platform_TA": {
        "bActive": AttributeType.boolean,
    },
    "TAGame.PRI_KnockOut_TA": {
        # "bIsActiveMVP": AttributeType.boolean, !!!
        "bIsEliminated": AttributeType.boolean,
        "Blocks": AttributeType.int_32,
        "DamageCaused": AttributeType.int_32,
        "EliminationOrder": AttributeType.int_32,
        "Grabs": AttributeType.int_32,
        "Hits": AttributeType.int_32,
        "KnockoutDeaths": AttributeType.int_32,
        "Knockouts": AttributeType.int_32,
        # "MatchPlacement": AttributeType.int_32,
    },
    "TAGame.PRI_TA": {
        # "bAbleToStart": AttributeType.boolean,
        # "BallDemolitions": AttributeType.int_32,
        # "BallDemolitionSaves": AttributeType.int_32,
        # "bBusy": AttributeType.boolean,
        "bIdleBanned": AttributeType.boolean,
        "bIsDistracted": AttributeType.boolean,
        "bIsInSplitScreen": AttributeType.boolean,
        # "bMatchAdmin": AttributeType.boolean,
        "bMatchMVP": AttributeType.boolean,
        "bOnlineLoadoutSet": AttributeType.boolean,
        "bOnlineLoadoutsSet": AttributeType.boolean,
        # "BotAvatarProductID": AttributeType.int_32,
        "BotBannerProductID": AttributeType.int_32,
        "BotProductName": AttributeType.int_32,
        "bReady": AttributeType.boolean,
        # "bStartVoteToForfeitDisabled": AttributeType.boolean,
        "bUsingBehindView": AttributeType.boolean,
        # "bUsingFreecam": AttributeType.boolean,
        "bUsingItems": AttributeType.boolean,
        "bUsingSecondaryCamera": AttributeType.boolean,
        "CameraPitch": AttributeType.uint_8,
        "CameraSettings": AttributeType.camera_settings,
        "CameraYaw": AttributeType.uint_8,
        "CarDemolitions": AttributeType.int_32,
        "ClientLoadout": AttributeType.loadout,
        "ClientLoadoutOnline": AttributeType.loadout_online,
        "ClientLoadouts": AttributeType.team_loadouts,
        "ClientLoadoutsOnline": AttributeType.loadouts_online,
        "ClubID": AttributeType.int_64,
        "CurrentVoiceRoom": AttributeType.string,
        # "KeepUpClears": AttributeType.int_32,
        # "KeepUpDenials": AttributeType.int_32,
        "KeepUpPossessions": AttributeType.int_32,
        "MatchAssists": AttributeType.int_32,
        "MatchBreakoutDamage": AttributeType.int_32,
        "MatchDemolishes": AttributeType.int_32,
        "MatchGoals": AttributeType.int_32,
        "MatchSaves": AttributeType.int_32,
        "MatchScore": AttributeType.int_32,
        "MatchShots": AttributeType.int_32,
        "MaxTimeTillItem": AttributeType.int_32,
        "PartyLeader": AttributeType.party_leader,
        "PawnType": AttributeType.uint_8,
        "PersistentCamera": AttributeType.pointer,
        # "PickupTimer": AttributeType.pointer,
        "PlayerHistoryKey": AttributeType.player_history_key,
        "PlayerHistoryValid": AttributeType.boolean,
        "PossessionClears": AttributeType.int_32,
        "PossessionDenials": AttributeType.int_32,
        "PossessionSteals": AttributeType.int_32,
        "PrimaryTitle": AttributeType.title,
        # "QuitSeverity": AttributeType.uint_8,
        # "ReplacingBotPRI": AttributeType.pointer,
        "ReplicatedGameEvent": AttributeType.pointer,
        "ReplicatedWorstNetQualityBeyondLatency": AttributeType.uint_8,
        "RepStatTitles": AttributeType.rep_stat_title,
        # "RespawnTimeRemaining": AttributeType.int_32,
        "SecondaryTitle": AttributeType.title,
        "SelfDemolitions": AttributeType.int_32,
        "SkillTier": AttributeType.skill_tier,
        "SpectatorShortcut": AttributeType.int_32,
        # "StayAsPartyVoter": AttributeType.pointer,
        # "StayAsPartyVoteYes": AttributeType.pointer,
        "SteeringSensitivity": AttributeType.float_32,
        "TimeTillItem": AttributeType.int_32,
        "Title": AttributeType.int_32,
        "TotalGameTimePlayed": AttributeType.float_32,
        "TotalIdleTime": AttributeType.float_32,
        "TotalXP": AttributeType.int_32,
        "ViralItemActor": AttributeType.pointer,
    },
    "TAGame.RBActor_TA": {
        "bFrozen": AttributeType.boolean,
        "bIgnoreSyncing": AttributeType.boolean,
        "bReplayActor": AttributeType.boolean,
        # "MaxAngularSpeed": AttributeType.float_32,
        # "MaxLinearSpeed": AttributeType.float_32,
        # "ReplicatedCollisionScale": AttributeType.float_32,
        # "ReplicatedGravityScale": AttributeType.float_32,
        "ReplicatedRBState": AttributeType.rigid_body,
        "TeleportCounter": AttributeType.uint_8,
        "WeldedInfo": AttributeType.welded_info,
    },
    "TAGame.RumblePickups_TA": {
        "AttachedPickup": AttributeType.pointer,
        "ConcurrentItemCount": AttributeType.int_32,
        "ConcurrentItemCount": AttributeType.int_32,
        "PickupInfo": AttributeType.pickup_info,
        # "PreviewTimeSeconds": AttributeType.int_32,
    },
    # "TAGame.Replay_Soccar_TA": {
    #     "bForfeit": AttributeType.boolean,
    #     "bLocalPlayerAbandoned": AttributeType.boolean,
    #     "bMatchCreatorAdminEnabled": AttributeType.boolean,
    #     "bNoContest": AttributeType.boolean,
    #     "bUnfairBots": AttributeType.boolean,
    #     "MatchStartEpoch": AttributeType.int_64,
    #     "PrimaryPlayerTeam": AttributeType.int_32,
    #     "Team0Score": AttributeType.int_32,
    #     "Team1Score": AttributeType.int_32,
    #     "TeamSize": AttributeType.int_32,
    #     "TotalSecondsPlayed": AttributeType.float_32,
    #     "UnfairTeamSize": AttributeType.int_32,
    #     "WinningTeam": AttributeType.int_32,
    # },
    "TAGame.SpecialPickup_BallFreeze_TA": {
        "RepOrigSpeed": AttributeType.float_32,
    },
    "TAGame.SpecialPickup_BallVelcro_TA": {
        "AttachTime": AttributeType.float_32,
        "bBroken": AttributeType.boolean,
        "bHit": AttributeType.boolean,
        "BreakTime": AttributeType.float_32,
    },
    "TAGame.SpecialPickup_Football_TA": {
        "WeldedBall": AttributeType.pointer,
    },
    "TAGame.SpecialPickup_Rugby_TA": {
        "bBallWelded": AttributeType.boolean,
    },
    # "TAGame.SpecialPickup_TA": {
    #     "CooldownSeconds": AttributeType.int_32,
    # },
    "TAGame.SpecialPickup_Targeted_TA": {
        "Targeted": AttributeType.pointer,
    },
    "TAGame.Stunlock_TA": {
        "Car": AttributeType.pointer,
        "MashTime": AttributeType.float_32,
        "MaxStunTime": AttributeType.float_32,
        "StunTimeRemaining": AttributeType.float_32,
    },
    "TAGame.Team_Soccar_TA": {
        "GameScore": AttributeType.int_32,
    },
    "TAGame.Team_TA": {
        "ClubColors": AttributeType.club_colors,
        "ClubID": AttributeType.int_64,
        "CustomTeamName": AttributeType.string,
        "Difficulty": AttributeType.int_32,
        "GameEvent": AttributeType.pointer,
        "LogoData": AttributeType.logo_data,
    },
    "TAGame.Vehicle_TA": {
        "bDriving": AttributeType.boolean,
        "bHasPostMatchCelebration": AttributeType.boolean,
        "bPodiumMode": AttributeType.boolean,
        "bReplicatedHandbrake": AttributeType.boolean,
        "InputRestriction": AttributeType.uint_8,
        # "PMCAnimIdx": AttributeType.int_32,
        # "PodiumSpot": AttributeType.int_32,
        "ReplicatedSteer": AttributeType.uint_8,
        "ReplicatedThrottle": AttributeType.uint_8,
    },
    "TAGame.VehiclePickup_TA": {
        "bNoPickup": AttributeType.boolean,
        "NewReplicatedPickupData": AttributeType.new_pickup,
        "ReplicatedPickupData": AttributeType.pickup,
    },
    "TAGame.ViralItemActor_TA": {
        "ClientFXInfectedType": AttributeType.uint_8,
        "InfectedStatus": AttributeType.uint_8,
    },
    # "TAGame.PickupTimer_TA": {
    #     "MaxTimeTillItem": AttributeType.int_32,
    #     "TimeTillItem": AttributeType.int_32,
    # },
    # "TAGame.GameEvent_KnockOut_TA": {
    #     "PlayerLives": AttributeType.int_32,
    #     "PodiumSpawnLocationZ": AttributeType.float_32,
    # },
    # "TAGame.Replay_TA": {
    #     "bIsUnfinishedMatchReplay": AttributeType.boolean,
    #     "BuildID": AttributeType.int_32,
    #     "BuildVersion": AttributeType.string,
    #     "Changelist": AttributeType.int_32,
    #     "Date": AttributeType.string,
    #     "GameVersion": AttributeType.int_32,
    #     "Id": AttributeType.string,
    #     "KeyframeDelay": AttributeType.float_32,
    #     "MapName": AttributeType.string,
    #     "MatchGuid": AttributeType.string,
    #     "MatchType": AttributeType.string,
    #     "MaxChannels": AttributeType.int_32,
    #     "MaxReplaySizeMB": AttributeType.int_32,
    #     "NumFrames": AttributeType.int_32,
    #     "PlayerName": AttributeType.string,
    #     "RecordFPS": AttributeType.float_32,
    #     "ReplayLastSaveVersion": AttributeType.int_32,
    #     "ReplayName": AttributeType.string,
    #     "ReplayVersion": AttributeType.int_32,
    #     "ReserveMegabytes": AttributeType.int_32,
    # },
    # "TAGame.SaveData_GameEditor_Training_TA": {
    #     "bPerfectCompleted": AttributeType.boolean,
    #     "bUnowned": AttributeType.boolean,
    #     "ShotsCompleted": AttributeType.int_32,
    #     "TrainingData": AttributeType.pointer,
    # },
    # "TAGame.TrainingEditorData_TA": {
    #     "Code": AttributeType.string,
    #     "CreatedAt": AttributeType.int_64,
    #     "CreatorName": AttributeType.string,
    #     "CreatorPlayerID": AttributeType.unique_id,
    #     "Description": AttributeType.string,
    #     "Difficulty": AttributeType.uint_8,
    #     "MapName": AttributeType.string,
    #     "TM_Guid": AttributeType.guid,
    #     "TM_Name": AttributeType.string,
    #     "Type": AttributeType.uint_8,
    #     "UpdatedAt": AttributeType.int_64,
    # },
    "TAGame.BallKeepUpComponent_TA": {
        "BallOwner": AttributeType.pointer,
        "KeepUpState": AttributeType.uint_8,
        "Score": AttributeType.int_32,
    },
    "TAGame.Ball_Spawner_TA": {
        "SpawnDelaySeconds": AttributeType.float_32,
        "SpawnedBall": AttributeType.pointer,
    },
    "TAGame.KeepUpIndicator_TA": {
        "ComponentOwner": AttributeType.pointer,
    },
    # "TAGame.VoteActor_TA": {
    #     "bFinished": AttributeType.boolean,
    #     "Counts": AttributeType.uint_8,
    #     "TimeRemaining": AttributeType.int_32,
    # }
}

_PARENT_MAP = {
    "Core.Object": {
        "Engine.Actor": {
            "Engine.Info": {
                "Engine.ReplicationInfo": {
                    "Engine.GameReplicationInfo": {
                        "ProjectX.GRI_X": {
                            "TAGame.GRI_TA": {
                                _gria("Basketball"): None,
                                _gria("Breakout"): None,
                                _gria("FootBall"): None,
                                _gria("FTE"): None,
                                _gria("GodBall"): None,
                                _gria("Hockey"): None,
                                _gria("Items"): None,
                                _gria("KnockOut"): None,
                                _gria("LTM_AprilFool"): None,
                                _gria("LTM_SpikeRush"): None,
                                _gria("LTM_SuperCube"): None,
                                _gria("Season"): None,
                                _gria("Soccar"): None,
                                _gria("Tutorial"): None,
                                _gria("LTM_BeachBall"): None,
                                _gria("HeatseekerTerritory"): None,
                                _gria("SnowDayTerritory"): None,
                                _gria("Territory"): None,
                                _gria("LTM_DropshotRumble"): None,
                                _gria("Possession"): None,
                                _gria("KnockOut", False): None,
                                _gria("Hops"): None,
                                _gria("LTM_SpeedDemon"): None,
                                _gria("SpikeDrop"): None,
                                _gria("MagnusFutball"): None,
                            },
                        },
                    },
                    "Engine.PlayerReplicationInfo": {
                        "ProjectX.PRI_X": {
                            "TAGame.PRI_TA": {
                                "TAGame.Default__PRI_TA": None,
                                "TAGame.PRI_Breakout_TA": {
                                    "TAGame.Default__PRI_Breakout_TA": None,
                                },
                                "TAGame.PRI_KnockOut_TA": {
                                    "TAGame.Default__PRI_KnockOut_TA": None,
                                },
                                "TAGame.PRI_Possession_TA": {
                                    "TAGame.Default__PRI_Possession_TA": None,
                                },
                            },
                        },
                    },
                    "ProjectX.NetModeReplicator_X": {
                        "ProjectX.Default__NetModeReplicator_X": None,
                    },
                    "TAGame.CameraSettingsActor_TA": {
                        "TAGame.Default__CameraSettingsActor_TA": None,
                    },
                    "TAGame.CarComponent_TA": {
                        "TAGame.CarComponent_AirActivate_TA": {
                            "TAGame.CarComponent_Boost_TA": {
                                "Archetypes.CarComponents.CarComponent_Boost": None,
                                "TAGame.CarComponent_Boost_KO_TA": {
                                    "Archetypes.KnockOut.GameEvent_Knockout:CarArchetype.Boost": None,
                                },
                            },
                            "TAGame.CarComponent_Dodge_TA": {
                                "Archetypes.CarComponents.CarComponent_Dodge": None,
                                "TAGame.CarComponent_Dodge_KO_TA": {
                                    "Archetypes.KnockOut.GameEvent_Knockout:CarArchetype.Dodge": None,
                                },
                            },
                            "TAGame.CarComponent_DoubleJump_TA": {
                                "Archetypes.CarComponents.CarComponent_DoubleJump": None,
                                "Archetypes.KnockOut.GameEvent_Knockout:CarArchetype.DoubleJump": None,
                                "TAGame.CarComponent_DoubleJump_KO_TA": None,
                                "TAGame.CarComponent_DoubleJump_Robin_TA": {
                                    "Archetypes.Mutators.Mutator_Robin:DoubleJump": None,
                                },
                            },
                        },
                        "TAGame.CarComponent_FlipCar_TA": {
                            "Archetypes.CarComponents.CarComponent_FlipCar": None,
                            "Archetypes.KnockOut.GameEvent_Knockout:CarArchetype.Flip": None,
                            "Archetypes.Mutators.Mutator_Robin:AutoFlip": None,
                        },
                        "TAGame.CarComponent_Jump_TA": {
                            "Archetypes.CarComponents.CarComponent_Jump": None,
                            "Archetypes.KnockOut.GameEvent_Knockout:CarArchetype.Jump": None,
                            "TAGame.CarComponent_Jump_Robin_TA": {
                                "Archetypes.Mutators.Mutator_Robin:Jump": None,
                            },
                        },
                        "TAGame.CarComponent_TerritoryDemolish_TA": {
                            "Archetypes.CarComponents.CarComponent_TerritoryDemolish": None,
                        },
                        "TAGame.CarComponent_Torque_TA": {
                            "Archetypes.KnockOut.GameEvent_Knockout:CarArchetype.Torque": None,
                        },
                        "TAGame.PickupTimer_TA": {
                            "TAGame.Default__PickupTimer_TA": None,
                        },
                        "TAGame.SpecialPickup_TA": {
                            "TAGame.SpecialPickup_BallGravity_TA": {
                                "Archetypes.SpecialPickups.SpecialPickup_GravityWell": None,
                                "TAGame.SpecialPickup_HauntedBallBeam_TA": {
                                    "Archetypes.SpecialPickups.SpecialPickup_HauntedBallBeam": None,
                                },
                            },
                            "TAGame.SpecialPickup_BallVelcro_TA": {
                                "Archetypes.SpecialPickups.SpecialPickup_BallVelcro": None,
                            },
                            "TAGame.SpecialPickup_Football_TA": {
                                "Archetypes.SpecialPickups.SpecialPickup_Football": None,
                            },
                            "TAGame.SpecialPickup_HitForce_TA": {
                                "Archetypes.SpecialPickups.SpecialPickup_StrongHit": None,
                            },
                            "TAGame.SpecialPickup_Rugby_TA": {
                                "Archetypes.SpecialPickups.SpecialPickup_Rugby": None,
                                "Archetypes.SpecialPickups.SpecialPickup_RugbyLightDark": None,
                            },
                            "TAGame.SpecialPickup_Targeted_TA": {
                                "TAGame.SpecialPickup_BallFreeze_TA": {
                                    "Archetypes.Mutators.SubRules.ItemsMode_RPS:DispenserArchetype.ItemPool.Obj_2": None,
                                    "Archetypes.SpecialPickups.SpecialPickup_BallFreeze": None,
                                    "Archetypes.SpecialPickups.BM.SpecialPickup_BallFreeze_BM": None,
                                },
                                "TAGame.SpecialPickup_BoostOverride_TA": {
                                    "Archetypes.SpecialPickups.SpecialPickup_BoostOverride": None,
                                },
                                "TAGame.SpecialPickup_GrapplingHook_TA": {
                                    "Archetypes.SpecialPickups.SpecialPickup_BallGrapplingHook": None,
                                },
                                "TAGame.SpecialPickup_Spring_TA": {
                                    "TAGame.SpecialPickup_BallCarSpring_TA": {
                                        "Archetypes.Mutators.SubRules.ItemsMode_RPS:DispenserArchetype.ItemPool.Obj": None,
                                        "Archetypes.Mutators.SubRules.ItemsMode_RPS:DispenserArchetype.ItemPool.Obj_1": None,
                                        "Archetypes.SpecialPickups.SpecialPickup_BallSpring": None,
                                        "Archetypes.SpecialPickups.SpecialPickup_CarSpring": None,
                                    },
                                    "TAGame.SpecialPickup_BallLasso_TA": {
                                        "Archetypes.SpecialPickups.SpecialPickup_BallLasso": None,
                                        "TAGame.SpecialPickup_Batarang_TA": {
                                            "Archetypes.SpecialPickups.SpecialPickup_Batarang": None,
                                        },
                                    },
                                },
                                "TAGame.SpecialPickup_Swapper_TA": {
                                    "Archetypes.SpecialPickups.SpecialPickup_Swapper": None,
                                },
                            },
                            "TAGame.SpecialPickup_Tornado_TA": {
                                "Archetypes.SpecialPickups.SpecialPickup_Tornado": None,
                            },
                        },
                    },
                    "TAGame.CrowdActor_TA": {
                        "TheWorld:PersistentLevel.CrowdActor_TA": None, # normalized
                    },
                    "TAGame.CrowdManager_TA": {
                        "TheWorld:PersistentLevel.CrowdManager_TA": None, # normalized
                    },
                    "TAGame.GameEvent_TA": {
                        "TAGame.GameEvent_Team_TA": {
                            "TAGame.GameEvent_Soccar_TA": {
                                "Archetypes.GameEvent.GameEvent_Basketball": None,
                                "Archetypes.GameEvent.GameEvent_Hockey": None,
                                "Archetypes.GameEvent.GameEvent_Items": None,
                                "Archetypes.GameEvent.GameEvent_Soccar": None,
                                "Archetypes.GameEvent.GameEvent_SoccarLan": None,
                                "GameInfo_Basketball.GameInfo.GameInfo_Basketball:Archetype": None,
                                "Gameinfo_Hockey.GameInfo.Gameinfo_Hockey:Archetype": None,
                                "GameInfo_LTM_AprilFool.GameInfo.GameInfo_LTM_AprilFool:Archetype": None,
                                "GameInfo_LTM_SpikeRush.GameInfo.GameInfo_LTM_SpikeRush:Archetype": None,
                                "GameInfo_LTM_SuperCube.GameInfo.GameInfo_LTM_SuperCube:Archetype": None,
                                "GameInfo_LTM_BeachBall.GameInfo.GameInfo_LTM_BeachBall:Archetype": None,
                                "GameInfo_HeatseekerTerritory.GameInfo.GameInfo_HeatseekerTerritory:Archetype": None,
                                "GameInfo_SnowDayTerritory.GameInfo.GameInfo_SnowDayTerritory:Archetype": None,
                                "GameInfo_Territory.GameInfo.GameInfo_Territory:Archetype": None,
                                "GameInfo_LTM_DropshotRumble.GameInfo.GameInfo_LTM_DropshotRumble:Archetype": None,
                                "GameInfo_Possession.GameInfo.GameInfo_Possession:Archetype": None,
                                "GameInfo_LTM_SpeedDemon.GameInfo.GameInfo_LTM_SpeedDemon:Archetype": None,
                                "GameInfo_SpikeDrop.GameInfo.GameInfo_SpikeDrop:Archetype": None,
                                "GameInfo_Hops.GameInfo.GameInfo_Hops:Archetype": None,
                                "GameInfo_MagnusFutball.GameInfo.GameInfo_MagnusFutball:Archetype": None,
                                "TAGame.GameEvent_Breakout_TA": {
                                    "Archetypes.GameEvent.GameEvent_Breakout": None,
                                },
                                "TAGame.GameEvent_Football_TA": {
                                    "GameInfo_FootBall.GameInfo.GameInfo_FootBall:Archetype": None,
                                },
                                "TAGame.GameEvent_FTE_TA": {
                                    "Archetypes.GameEvent.GameEvent_FTE_Part1_Prime": None,
                                },
                                "TAGame.GameEvent_GodBall_TA": {
                                    "GameInfo_GodBall.GameInfo.GameInfo_GodBall:Archetype": None,
                                },
                                "TAGame.GameEvent_KnockOut_TA": {
                                    "Archetypes.KnockOut.GameEvent_Knockout": None,
                                },
                                "TAGame.GameEvent_Season_TA": {
                                    "Archetypes.GameEvent.GameEvent_Season": None,
                                },
                                "TAGame.GameEvent_SoccarPrivate_TA": {
                                    "Archetypes.GameEvent.GameEvent_BasketballPrivate": None,
                                    "Archetypes.GameEvent.GameEvent_HockeyPrivate": None,
                                    "Archetypes.GameEvent.GameEvent_SoccarPrivate": None,
                                    "TAGame.GameEvent_SoccarSplitscreen_TA": {
                                        "Archetypes.GameEvent.GameEvent_BasketballSplitscreen": None,
                                        "Archetypes.GameEvent.GameEvent_HockeySplitscreen": None,
                                        "Archetypes.GameEvent.GameEvent_SoccarSplitscreen": None,
                                    },
                                },
                                "TAGame.GameEvent_Tutorial_TA": {
                                    "TAGame.GameEvent_Training_TA": {
                                        "TAGame.GameEvent_Training_Aerial_TA": {
                                            "GameInfo_Tutorial.GameEvent.GameEvent_Tutorial_Aerial": None,
                                        },
                                        "TAGame.GameEvent_Training_Goalie_TA": {
                                            "GameInfo_Tutorial.GameEvent.GameEvent_Tutorial_Goalie": None,
                                        },
                                        "TAGame.GameEvent_Training_Striker_TA": {
                                            "GameInfo_Tutorial.GameEvent.GameEvent_Tutorial_Striker": None,
                                        },
                                    },
                                    "TAGame.GameEvent_Tutorial_Basic_TA": {
                                        "Archetypes.GameEvent.GameEvent_Tutorial_Basic": None,
                                        "TAGame.GameEvent_Tutorial_Advanced_TA": {
                                            "Archetypes.GameEvent.GameEvent_Tutorial_Advanced": None,
                                        },
                                    },
                                    "TAGame.GameEvent_Tutorial_FreePlay_TA": {
                                        "Archetypes.GameEvent.GameEvent_Tutorial_FreePlay": None,
                                    },
                                },
                                "TAGame.GameEvent_Territory_TA": None,
                            },
                        },
                    },
                    "TAGame.VehiclePickup_TA": {
                        "TAGame.VehiclePickup_Boost_TA": {
                            "TheWorld:PersistentLevel.VehiclePickup_Boost_TA": None, # normalized
                        },
                    },
                },
                "Engine.TeamInfo": {
                    "TAGame.Team_TA": {
                        "TAGame.Team_Soccar_TA": {
                            "Archetypes.Teams.Team": None, # normalized
                            "TAGame.Team_Freeplay_TA": {
                                "Archetypes.Teams.TeamWhite": None, # normalized
                            },
                        },
                    },
                },
                "Engine.ZoneInfo": {
                    "Engine.WorldInfo": None,
                },
            },
            "Engine.NavigationPoint": {
                "Engine.PlayerStart": None,
            },
            "Engine.Pawn": {
                "ProjectX.Pawn_X": {
                    "TAGame.RBActor_TA": {
                        "TAGame.Ball_TA": {
                            "Archetypes.Ball.Ball_PizzaPuck": None,
                            "Archetypes.Ball.ball_luminousairplane": None,
                            "Archetypes.Ball.Ball_Anniversary": None,
                            "Archetypes.Ball.Ball_Basketball": None,
                            "Archetypes.Ball.Ball_BasketBall": None,
                            "Archetypes.Ball.Ball_BasketBall_Mutator": None,
                            "Archetypes.Ball.Ball_Beachball": None,
                            "Archetypes.Ball.Ball_Default": None,
                            "Archetypes.Ball.Ball_Ekin": None,
                            "Archetypes.Ball.Ball_Football": None,
                            "Archetypes.Ball.Ball_Puck": None,
                            "Archetypes.Ball.CubeBall": None,
                            "Archetypes.Ball.Ball_Shoe": None,
                            "Archetypes.Ball.Ball_SpookyBalloon": None,
                            "Archetypes.Ball.Ball_Strike": None,
                            "TAGame.Ball_Breakout_TA": {
                                "Archetypes.Ball.Ball_Breakout": None,
                                "Archetypes.Ball.Ball_Score": None,
                            },
                            "TAGame.Ball_God_TA": {
                                "Archetypes.Ball.Ball_God": None,
                                "TAGame.Ball_Fire_TA": {
                                    "Archetypes.Ball.Ball_Fire_Obstacle": None,
                                    "Archetypes.Ball.Ball_Fire": None,
                                },
                            },
                            "TAGame.Ball_Haunted_TA": {
                                "Archetypes.Ball.Ball_Haunted": None,
                            },
                            "TAGame.Ball_Trajectory_TA": {
                                "Archetypes.Ball.Ball_Trajectory": None,
                            },
                            "TAGame.Ball_Tutorial_TA": {
                                "Archetypes.Ball.Ball_Training": None,
                                "Archetypes.Ball.Ball_Tutorial": None,
                            },
                        },
                        "TAGame.Vehicle_TA": {
                            "TAGame.Car_TA": {
                                "Archetypes.Car.Car_Default": None,
                                "TAGame.Car_Freeplay_TA": {
                                    "Archetypes.Car.Car_PostGameLobby": None,
                                    "Mutators.Mutators.Mutators.FreePlay:CarArchetype": None,
                                    "Mutators.Mutators.Mutators.OnlineFreeplay:CarArchetype": None,
                                },
                                "TAGame.Car_KnockOut_TA": {
                                    "Archetypes.KnockOut.GameEvent_Knockout:CarArchetype": None,
                                },
                                "TAGame.Car_Season_TA": {
                                    "Archetypes.GameEvent.GameEvent_Season:CarArchetype": None,
                                },
                                "TAGame.Default__Car_TA": None,
                            },
                        },
                    },
                },
            },
            "Engine.ReplicatedActor_ORS": {
                "TAGame.MaxTimeWarningData_TA": {
                    "TAGame.Default__MaxTimeWarningData_TA": None,
                },
                "TAGame.BallKeepUpComponent_TA": {
                    "Archetypes.Ball.BallComponent_KeepUp": None,
                },
            },
            "TAGame.BreakOutActor_Platform_TA": {
                "TheWorld:PersistentLevel.BreakOutActor_Platform_TA": None, # normalized
            },
            "TAGame.Cannon_TA": {
                "Archetypes.Tutorial.Cannon": None,
            },
            "TAGame.DynamicMeshActor_TA": {
                "TAGame.HauntedBallTrapTrigger_TA": {
                    "TheWorld:PersistentLevel.HauntedBallTrapTrigger_TA": None, # normalized
                },
                "TAGame.TrackerWallDynamicMeshActor_TA": {
                    "TAGame.Default__TrackerWallDynamicMeshActor_TA": None,
                },
            },
            "TAGame.FreeplayCommands_TA": {
                "TAGame.Default__FreeplayCommands_TA": None,
            },
            "TAGame.InMapScoreboard_TA": {
                "TheWorld:PersistentLevel.InMapScoreboard_TA": None, # normalized
            },
            "TAGame.PlayerStart_Platform_TA": {
                "TheWorld:PersistentLevel.PlayerStart_Platform_TA": None, # normalized
            },
            "TAGame.RumblePickups_TA": {
                "TAGame.Default__RumblePickups_TA": None,
            },
            "TAGame.ViralItemActor_TA": {
                "TAGame.Default__ViralItemActor_TA": None,
            },
            "TAGame.Stunlock_TA": {
                "Archetypes.KnockOut.GameEvent_Knockout:CarArchetype.StunlockArchetype": None,
            },
            "TAGame.Ball_Spawner_TA": {
                "Archetypes.Ball.Ball_RingSpawner": None,
            },
            "TAGame.KeepUpIndicator_TA": {
                "Archetypes.Misc.KeepUpIndicator": None,
            },
        },
        "TAGame.ProductAttribute_TA": {
            # "TAGame.ProductAttribute_Blueprint_TA": None,
            # "TAGame.ProductAttribute_BlueprintCost_TA": None,
            # "TAGame.ProductAttribute_Certified_TA": None,
            # "TAGame.ProductAttribute_NoNotify_TA": None,
            "TAGame.ProductAttribute_Painted_TA": None,
            # "TAGame.ProductAttribute_Quality_TA": None,
            "TAGame.ProductAttribute_SpecialEdition_TA": None,
            "TAGame.ProductAttribute_TeamEdition_TA": None,
            "TAGame.ProductAttribute_TitleID_TA": None,
            "TAGame.ProductAttribute_UserColor_TA": None,
        },
        "TAGame.Replay_TA": {
            "TAGame.Replay_Soccar_TA": None,
        },
        "TAGame.SaveData_GameEditor_Training_TA": None,
        "TAGame.TrainingEditorData_TA": None,
        "TAGame.CameraTrackPoint_TA": None,
        "TAGame.CameraTrack_TA": None,
    },
    "TAGame.VoteActor_TA": {
        "TAGame.Default__VoteActor_TA": None,
    },
}


CLASS_INFO = ClassHierarchy.build(_SPAWNS, _ATTRIBUTES, _PARENT_MAP)
