#include "pc/guest/image.h"
const unsigned Memories_GameFingerprint = 0xad6fcc3cu;
void GsGetTimInfo(void) { Memories_Unimplemented("GsGetTimInfo"); }
void InitCARD(void) { Memories_Unimplemented("InitCARD"); }
void PCclose(void) { Memories_Unimplemented("PCclose"); }
void PClseek(void) { Memories_Unimplemented("PClseek"); }
void PCopen(void) { Memories_Unimplemented("PCopen"); }
void PCread(void) { Memories_Unimplemented("PCread"); }
void Psx_close(void) { Memories_Unimplemented("Psx_close"); }
void Psx_exit(void) { Memories_Unimplemented("Psx_exit"); }
void Psx_lseek(void) { Memories_Unimplemented("Psx_lseek"); }
void Psx_open(void) { Memories_Unimplemented("Psx_open"); }
void Psx_read(void) { Memories_Unimplemented("Psx_read"); }
void Psx_write(void) { Memories_Unimplemented("Psx_write"); }
void StartCARD(void) { Memories_Unimplemented("StartCARD"); }
void _bu_init(void) { Memories_Unimplemented("_bu_init"); }
void _card_clear(void) { Memories_Unimplemented("_card_clear"); }
void _card_info(void) { Memories_Unimplemented("_card_info"); }
void _card_load(void) { Memories_Unimplemented("_card_load"); }
void _card_read(void) { Memories_Unimplemented("_card_read"); }
void _card_status(void) { Memories_Unimplemented("_card_status"); }
void _card_wait(void) { Memories_Unimplemented("_card_wait"); }
void _card_write(void) { Memories_Unimplemented("_card_write"); }
void _new_card(void) { Memories_Unimplemented("_new_card"); }
void firstfile(void) { Memories_Unimplemented("firstfile"); }
void func_800158C8(void) { Memories_Unimplemented("func_800158C8"); }
void func_80021EA4(void) { Memories_Unimplemented("func_80021EA4"); }
void func_8004EB9C(void) { Memories_Unimplemented("func_8004EB9C"); }
void func_80065B24(void) { Memories_Unimplemented("func_80065B24"); }
void func_80065BFC(void) { Memories_Unimplemented("func_80065BFC"); }
void func_80066574(void) { Memories_Unimplemented("func_80066574"); }
void nextfile(void) { Memories_Unimplemented("nextfile"); }
extern void AiScript_Add(void);
extern void AiScript_AddCard(void);
extern void AiScript_AddType(void);
extern void AiScript_CalcCardPower(void);
extern void AiScript_Call(void);
extern void AiScript_CheckRitual(void);
extern void AiScript_ClearCards(void);
extern void AiScript_ClearSelectionRandom(void);
extern void AiScript_ClearTypes(void);
extern void AiScript_CountCards(void);
extern void AiScript_EndField(void);
extern void AiScript_EndHand(void);
extern void AiScript_EvaluateFusion(void);
extern void AiScript_FieldNop(void);
extern void AiScript_FindBestAttack(void);
extern void AiScript_FindBestCombo(void);
extern void AiScript_FindCard(void);
extern void AiScript_FindDefenseStopper(void);
extern void AiScript_FindEquipTarget(void);
extern void AiScript_FindFirstCard(void);
extern void AiScript_FindFirstMonster(void);
extern void AiScript_FindFirstType(void);
extern void AiScript_FindKiller(void);
extern void AiScript_FindStrongest(void);
extern void AiScript_FindWeakest(void);
extern void AiScript_HandNop(void);
extern void AiScript_Init(void);
extern void AiScript_Jump(void);
extern void AiScript_JumpBetween(void);
extern void AiScript_JumpEqual(void);
extern void AiScript_JumpGreater(void);
extern void AiScript_JumpGreaterEqual(void);
extern void AiScript_JumpNotEqual(void);
extern void AiScript_JumpRandom(void);
extern void AiScript_LoadBestAttacker(void);
extern void AiScript_LoadBestDifference(void);
extern void AiScript_LoadBestTarget(void);
extern void AiScript_LoadCardID(void);
extern void AiScript_LoadCardType(void);
extern void AiScript_LoadDeckSize(void);
extern void AiScript_LoadGuardianStarChoice(void);
extern void AiScript_LoadLifePoint(void);
extern void AiScript_LoadOpponentData(void);
extern void AiScript_LoadOpponentID(void);
extern void AiScript_LoadSelectionRandom(void);
extern void AiScript_LoadTerrain(void);
extern void AiScript_MatchType(void);
extern void AiScript_MoveCard(void);
extern void AiScript_PlayFaceUp(void);
extern void AiScript_PlayFieldCard(void);
extern void AiScript_Print(void);
extern void AiScript_PushComboCard(void);
extern void AiScript_PushComboEmpty(void);
extern void AiScript_ReadByte(void);
extern void AiScript_ReadShort(void);
extern void AiScript_Return(void);
extern void AiScript_Run(void);
extern void AiScript_SetFaceDown(void);
extern void AiScript_SetPosition(void);
extern void AiScript_SetRandom(void);
extern void AiScript_SetRegister(void);
extern void AiScript_SetSelectionRandom(void);
extern void AiScript_SkipField(void);
extern void AiScript_SkipHand(void);
extern void AiScript_StartCombo(void);
extern void AiScript_Store(void);
extern void AiScript_Subtract(void);
extern void AiScript_TestHighStat(void);
extern void AiScript_TestPinned(void);
extern void Ai_CompleteFusion(void);
extern void Ai_GetCardRange(void);
extern void Ai_GetHandSize(void);
extern void Ai_GetWinningCardRange(void);
extern void Ai_IsCardInSet(void);
extern void Ai_IsCardInSets(void);
extern void Ai_IsTypeInSet(void);
extern void ApplyMatrix(void);
extern void ApplyMatrixLV(void);
extern void ApplyMatrixSV(void);
extern void AverageZ3(void);
extern void AverageZ4(void);
extern void BuildDeck_AddCard(void);
extern void BuildDeck_CompareCard(void);
extern void BuildDeck_DrawSortIcons(void);
extern void BuildDeck_EnterNarrowConfirmMode(void);
extern void BuildDeck_EnterWideConfirmMode(void);
extern void BuildDeck_GetActiveCardID(void);
extern void BuildDeck_HasOpenDeckSlot(void);
extern void BuildDeck_RefreshCountDisplay(void);
extern void BuildDeck_ReturnCardToChest(void);
extern void BuildDeck_TakeCardFromChest(void);
extern void BuildDeck_TestAndSetInitialized(void);
extern void BuildDeck_UpdateCardListInput(void);
extern void BuildDeck_UpdateChestPaneInput(void);
extern void BuildDeck_UpdateDeckPaneInput(void);
extern void BuildDeck_UpdatePaneTransition(void);
extern void CampaignMap_ClearLocationObjects(void);
extern void CampaignMap_CreateLocationLabel(void);
extern void CampaignMap_CreateLocationMarker(void);
extern void CampaignMap_LoadPackageStage(void);
extern void CampaignMap_MoveCameraDpad(void);
extern void CampaignMap_PickAlternateExit(void);
extern void CampaignMap_PickExit(void);
extern void CampaignMap_RebuildLocationObjects(void);
extern void CampaignMap_ResetCamera(void);
extern void CampaignMap_SetCameraFromLocation(void);
extern void CampaignMap_SetLocation(void);
extern void CampaignMap_StartCameraTween(void);
extern void CampaignMap_UpdateAlternateLocation(void);
extern void CampaignMap_UpdateLocation(void);
extern void CampaignMap_UpdateLocationTransition(void);
extern void CampaignMap_UpdateView(void);
extern void Campaign_CreatePrimaryDisplayObject(void);
extern void Campaign_EnsureStoryFlag(void);
extern void Campaign_LoadScenePackage(void);
extern void Campaign_LoadScenePackageStage(void);
extern void Campaign_TestStoryFlag(void);
extern void CardList_CreateSlotTextBox(void);
extern void CardList_RenderDeckBoxStats(void);
extern void CardList_UpdateSortMode(void);
extern void CardPreview_UpdateVariant(void);
extern void CdControlB(void);
extern void CdFlush(void);
extern void CdGetSector(void);
extern void CdIntToPos_8007E600(void);
extern void CdMix(void);
extern void CdPosToInt(void);
extern void CdPosToInt_8007E710(void);
extern void CdReadyCallback(void);
extern void ChangeClearPAD(void);
extern void Checkerboard_DrawBackground(void);
extern void ClearImage(void);
extern void CloseEvent(void);
extern void Color_HslToRgb(void);
extern void Color_RgbToHsl(void);
extern void Color_TintBgr555Pixel(void);
extern void DebugMenu_DimPrimaryDisplayObject(void);
extern void DebugMenu_EnterDeckEditor(void);
extern void DebugMenu_EnterDuel(void);
extern void DebugMenu_EnterMappedMode(void);
extern void DebugMenu_Exit(void);
extern void DebugMenu_Init(void);
extern void DebugMenu_ResetEntryState(void);
extern void DebugMenu_RestorePrimaryDisplayObject(void);
extern void DebugMenu_Update(void);
extern void DebugMenu_UpdateBustUpEntry(void);
extern void DebugMenu_UpdateCampaignEntry(void);
extern void DebugMenu_UpdateCursorLayout(void);
extern void DebugMenu_UpdateLoadEntry(void);
extern void DebugMenu_UpdateMovieEntry(void);
extern void DebugMenu_UpdateSaveEntry(void);
extern void DebugMenu_UpdateSoundEntry(void);
extern void DebugMenu_UpdateTitleEntry(void);
extern void DebugMenu_UpdateTradeEntry(void);
extern void DebugMenu_UpdateTwoPlayerDuelEntry(void);
extern void DecDCTReset(void);
extern void DecDCTin(void);
extern void DecDCTout(void);
extern void DecDCToutCallback(void);
extern void DecDCTvlc2(void);
extern void DecDCTvlcBuild(void);
extern void Dialog_HighlightChoice(void);
extern void Dialog_OpenChoice(void);
extern void Dialog_ReadChoiceInput(void);
extern void Dialog_UpdateChoice(void);
extern void DisableEvent(void);
extern void DisplayEffect_BuildResourceObjects(void);
extern void DisplayEffect_HasResourceEntry(void);
extern void DisplayEffect_LoadResourceStage(void);
extern void DisplayEffect_ProcessMenuRecords(void);
extern void DisplayEffect_UpdateMenuRecord(void);
extern void DisplayObjectFade_MarkInitialized(void);
extern void DisplayObjectFade_ReleaseChannel(void);
extern void DisplayObjectStream_ConfigureRotation(void);
extern void DisplayObjectStream_JumpToOffset(void);
extern void DisplayObjectStream_JumpToRandomOffset(void);
extern void DisplayObjectStream_Noop(void);
extern void DisplayObjectStream_ReadNextCommand(void);
extern void DisplayObjectStream_ReadU16LE(void);
extern void DisplayObjectStream_ResetOffset(void);
extern void DisplayObjectStream_ResolveOffset(void);
extern void DisplayObjectStream_Stop(void);
extern void DisplayObjectStream_ToggleFlagAndJumpToOffset(void);
extern void DisplayObject_AcquireSlot(void);
extern void DisplayObject_ConfigureScreenSprite(void);
extern void DisplayObject_ConfigureSpriteAtPosition(void);
extern void DisplayObject_ConfigureSpriteAtPositionWithResource(void);
extern void DisplayObject_ConfigureSpriteResource(void);
extern void DisplayObject_ConfigureSpriteWithResource(void);
extern void DisplayObject_CopyWorkSlots(void);
extern void DisplayObject_FadeBrightnessAndRelease(void);
extern void DisplayObject_FindAllocatedByTag(void);
extern void DisplayObject_FindFreeGeneralSlot(void);
extern void DisplayObject_FindFreeSlot(void);
extern void DisplayObject_InitializeGouraudQuad(void);
extern void DisplayObject_InitializeTexturedGouraudQuad(void);
extern void DisplayObject_InterpolatePositionCosine(void);
extern void DisplayObject_MarkInitialized(void);
extern void DisplayObject_MoveToListHead(void);
extern void DisplayObject_Release(void);
extern void DisplayObject_ReleaseIfPresent(void);
extern void DisplayObject_RenderFrame(void);
extern void DisplayObject_RenderGouraudQuadList(void);
extern void DisplayObject_RenderSpotlightMask(void);
extern void DisplayObject_RenderSpriteList(void);
extern void DisplayObject_RenderSpriteSheet(void);
extern void DisplayObject_RenderSpriteSheetList(void);
extern void DisplayObject_RenderSpriteStripList(void);
extern void DisplayObject_RenderSpriteStrips(void);
extern void DisplayObject_RenderTexturedGouraudQuadList(void);
extern void DisplayObject_Reset(void);
extern void DisplayObject_ResetPool(void);
extern void DisplayObject_ResetVelocity(void);
extern void DisplayObject_RunSecondaryCallbackList(void);
extern void DisplayObject_RunUpdateAndCheckRenderable(void);
extern void DisplayObject_RunUpdateCallbackList(void);
extern void DisplayObject_SavePosition(void);
extern void DisplayObject_SelectOrderingTable1(void);
extern void DisplayObject_SelectOrderingTable3(void);
extern void DisplayObject_SetDepthOffset(void);
extern void DisplayObject_SetResourcePath(void);
extern void DisplayObject_SetResourceVariant(void);
extern void DisplayObject_SetResourceVariantFromSign(void);
extern void DisplayObject_StepPositionX(void);
extern void DisplayObject_StepPositionXY(void);
extern void DisplayObject_StepPositionXYZ(void);
extern void DisplayObject_StepPositionY(void);
extern void DisplayObject_StepPositionZ(void);
extern void DisplayObject_StepToward(void);
extern void DisplayObject_StepTowardZero(void);
extern void DisplayObject_SubmitPacket(void);
extern void DisplayObject_UpdateAlphaTransition(void);
extern void DisplayObject_UpdateCommandStream(void);
extern void DisplayObject_UpdateResourceVariant(void);
extern void DisplayPositionGroup_SetPosition(void);
extern void DivideFT4(void);
extern void DrawOTag(void);
extern void DrawSync(void);
extern void DsCommand(void);
extern void DsEndReadySystem(void);
extern void DsInit(void);
extern void DsPacket(void);
extern void DsRead2(void);
extern void DsReadySystemMode(void);
extern void DsSearchFile(void);
extern void DsStartReadySystem(void);
extern void DuelCard_CanActThisTurn(void);
extern void DuelCard_CaptureRoundedTexture(void);
extern void DuelCard_DeactivateRecord(void);
extern void DuelCard_DecodeTaggedSlotIndex(void);
extern void DuelCard_RemoveFromField(void);
extern void DuelCard_UpdateDefenseRotation(void);
extern void DuelEffect_AllocateRequest(void);
extern void DuelEffect_AppendEntry(void);
extern void DuelEffect_ApplyBoardDestruction(void);
extern void DuelEffect_ApplyCursebreaker(void);
extern void DuelEffect_ApplyDarkPiercingLight(void);
extern void DuelEffect_ApplyDirectDamage(void);
extern void DuelEffect_ApplyHarpiesFeatherDuster(void);
extern void DuelEffect_ApplyLifePointRecovery(void);
extern void DuelEffect_ApplyMonsterRemoval(void);
extern void DuelEffect_ApplyRaigeki(void);
extern void DuelEffect_ApplyRitual(void);
extern void DuelEffect_ApplyStatPenalty(void);
extern void DuelEffect_ApplyStopDefense(void);
extern void DuelEffect_ApplySwords(void);
extern void DuelEffect_ApplyTerrain(void);
extern void DuelEffect_ClearCardEffect(void);
extern void DuelEffect_ClearMatchingMarker(void);
extern void DuelEffect_ClearResourceObjectPointers(void);
extern void DuelEffect_CreateChannel(void);
extern void DuelEffect_CreateRequest(void);
extern void DuelEffect_FadeOutBgmCommand(void);
extern void DuelEffect_FindFreeRequest(void);
extern void DuelEffect_HasActiveEntry(void);
extern void DuelEffect_InitEntry(void);
extern void DuelEffect_InitEntryDefaultFlags(void);
extern void DuelEffect_MarkInitialized(void);
extern void DuelEffect_MarkObjectIfActive(void);
extern void DuelEffect_MarkStateInitialized(void);
extern void DuelEffect_PlayBgmCommand(void);
extern void DuelEffect_PlaySoundCommand(void);
extern void DuelEffect_ProcessBgmCommand(void);
extern void DuelEffect_ProcessEntries(void);
extern void DuelEffect_ResetEntryMarkers(void);
extern void DuelEffect_ResetOccupancy(void);
extern void DuelEffect_ResetRequestPool(void);
extern void DuelEffect_SetEntryRangeLayout(void);
extern void DuelEffect_StartCardEffect(void);
extern void DuelEffect_StartRitual(void);
extern void DuelEffect_StartSwords(void);
extern void DuelEffect_UpdateCardEffect(void);
extern void DuelEffect_UpdateCardViewerState(void);
extern void DuelEffect_UpdateDialogState(void);
extern void DuelEffect_UpdateObjectLayout(void);
extern void DuelEffect_UpdateRequests(void);
extern void DuelEffect_UpdateRevealCard(void);
extern void DuelEffect_UpdateState(void);
extern void DuelResult_UpdateOrbitSprite(void);
extern void DuelScene_Update(void);
extern void DuelScene_UpdateBattle(void);
extern void DuelScene_UpdateCardPlacement(void);
extern void DuelScene_UpdateCardUse(void);
extern void DuelScene_UpdateDrawPhase(void);
extern void DuelScene_UpdateDrawResolution(void);
extern void DuelScene_UpdateEffectPreview(void);
extern void DuelScene_UpdateExodiaResult(void);
extern void DuelScene_UpdateFieldActions(void);
extern void DuelScene_UpdateHandActions(void);
extern void DuelScene_UpdateResultOutro(void);
extern void DuelScene_UpdateResultRewards(void);
extern void DuelScene_UpdateResume(void);
extern void DuelScene_UpdateStartup(void);
extern void DuelScene_UpdateTurnSwitch(void);
extern void DuelScene_UpdateWithSideInput(void);
extern void DuelSelection_LinkDisplayObject(void);
extern void DuelSelection_LinkDisplayObjects(void);
extern void DuelSelection_UpdateLinkedObject(void);
extern void Duel_ApplyCardObjectFlags(void);
extern void Duel_AwardCard(void);
extern void Duel_CalcBattleAttack(void);
extern void Duel_CalcBattleDefense(void);
extern void Duel_CalcCardStats(void);
extern void Duel_CalcGuardianStarBonus(void);
extern void Duel_CalcGuardianStarMatchup(void);
extern void Duel_CalcRankScore(void);
extern void Duel_CalcRankScoreChange(void);
extern void Duel_CheckEquip(void);
extern void Duel_CheckFusion(void);
extern void Duel_CheckQuitInput(void);
extern void Duel_CheckRitual(void);
extern void Duel_ClearHandSlots(void);
extern void Duel_CollectFieldCardsBelowType(void);
extern void Duel_CollectFieldCardsByType(void);
extern void Duel_CollectFieldRowCardObjects(void);
extern void Duel_CollectMatchingFieldCardObjects(void);
extern void Duel_CreateCardEffectOverlay(void);
extern void Duel_DrawCardAtOutputPosition(void);
extern void Duel_DrawFieldCards(void);
extern void Duel_DrawLifePointsAndDeckCounts(void);
extern void Duel_FindFreeFieldSlot(void);
extern void Duel_FindPlayerDeckCard(void);
extern void Duel_GetBaseCardStat(void);
extern void Duel_GetCardEffectVariant(void);
extern void Duel_GetCardViewerRequestId(void);
extern void Duel_GetTerrainBoost(void);
extern void Duel_HasAllExodiaPieces(void);
extern void Duel_InitModelScene(void);
extern void Duel_InitScene(void);
extern void Duel_InitSelectionRecords(void);
extern void Duel_InitSideStates(void);
extern void Duel_IsPlayerDeckComplete(void);
extern void Duel_LoadPackageStage(void);
extern void Duel_LoadTerrainPackage(void);
extern void Duel_PopulateCombinedDeckData(void);
extern void Duel_RequestCombinedDeckData(void);
extern void Duel_ResetCardRecords(void);
extern void Duel_SelectAttackTrap(void);
extern void Duel_SelectCardDrop(void);
extern void Duel_SelectEquipPair(void);
extern void Duel_SelectTrapByCardId(void);
extern void Duel_SelectTrapPlay(void);
extern void Duel_SetupCardRecord(void);
extern void Duel_ShowResultPage(void);
extern void Duel_ShuffleBothDecks(void);
extern void Duel_ShuffleDeck(void);
extern void Duel_StepCardDataTransfer(void);
extern void Duel_UpdateCardPickCursor(void);
extern void Duel_UpdateDrawCardSlide(void);
extern void Duel_UpdateLifePointDisplay(void);
extern void Duel_UpdateTrapPresentation(void);
extern void EnableEvent(void);
extern void EnterCriticalSection(void);
extern void ExitCriticalSection(void);
extern void Fade_DisableOrderingTables(void);
extern void Fade_DrawOverlay(void);
extern void Fade_EnableOrderingTables(void);
extern void Fade_FillBandLevels(void);
extern void Fade_Init(void);
extern void Fade_InitIn(void);
extern void Fade_InitInColor(void);
extern void Fade_InitOut(void);
extern void Fade_InitOutColor(void);
extern void Fade_SetLevel(void);
extern void Fade_SetTargetLevel(void);
extern void Fade_StartIn(void);
extern void Fade_StartInKeepOverlay(void);
extern void Fade_StartInKeepOverlayAndHideSecondaryTables(void);
extern void Fade_StartOut(void);
extern void Fade_StartOutKeepOverlay(void);
extern void Fade_StartOutKeepOverlayAndHideSecondaryTables(void);
extern void Fade_StepBands(void);
extern void Fade_Update(void);
extern void Fade_Wait(void);
extern void Fade_WaitIn(void);
extern void Fade_WaitInitIn(void);
extern void Fade_WaitInitInColor(void);
extern void Fade_WaitInitOut(void);
extern void Fade_WaitInitOutColor(void);
extern void Fade_WaitOut(void);
extern void File_ActivateTransfer(void);
extern void File_Exists(void);
extern void File_GetPosition(void);
extern void File_InitTransferDescriptor(void);
extern void File_InitTransferState(void);
extern void File_RequestAsyncTransfer(void);
extern void File_RequestEgyptOverworldPackage(void);
extern void File_RequestGameOverPackage(void);
extern void File_RequestMainMenuPackage(void);
extern void File_RequestNameEntryPackage(void);
extern void File_RequestOptionsPackage(void);
extern void File_RequestPasswordPackage(void);
extern void File_RequestSecondaryAsyncTransfer(void);
extern void File_RequestSecondaryRangeTransfer(void);
extern void File_ServiceTransfers(void);
extern void File_SetPositionTable(void);
extern void File_SetTransferLocation(void);
extern void File_StepActiveTransfer(void);
extern void File_TransferReadyCallback(void);
extern void File_TryRequestAsyncTransfer(void);
extern void File_TryStartPrimaryTransfer(void);
extern void File_WaitForTransfers(void);
extern void FntFlush(void);
extern void FntLoad(void);
extern void FntOpen(void);
extern void FntPrint(void);
extern void FreeDuel_Entry(void);
extern void FreeDuel_GetSparkleSlot(void);
extern void FreeDuel_Init(void);
extern void FreeDuel_LoadPackageStage(void);
extern void FreeDuel_PlaceCursor(void);
extern void FreeDuel_SpawnSparkle(void);
extern void FreeDuel_UpdateCursorTween(void);
extern void FreeDuel_UpdateScreen(void);
extern void FreeDuel_UpdateScrollbar(void);
extern void FreeDuel_UpdateSparkle(void);
extern void GameOver_Init(void);
extern void GameOver_LoadPackageStage(void);
extern void GetClut(void);
extern void GetDispEnv(void);
extern void GetDrawEnv(void);
extern void GetRCnt(void);
extern void GetTPage(void);
extern void GetVideoMode(void);
extern void Graphics_BeginFrame(void);
extern void Graphics_SubmitTextureWindowPacket(void);
extern void Graphics_SyncFrame(void);
extern void GsClearOt(void);
extern void GsDefDispBuff(void);
extern void GsDrawOt(void);
extern void GsGetActiveBuff(void);
extern void GsGetHeadpUnit(void);
extern void GsGetLs(void);
extern void GsGetLsUnit(void);
extern void GsGetLwUnit(void);
extern void GsGetLwsUnit(void);
extern void GsInit3D(void);
extern void GsInitGraph(void);
extern void GsInitGraph2(void);
extern void GsInitVcount(void);
extern void GsLinkAnim(void);
extern void GsMapCoordUnit(void);
extern void GsMapUnit(void);
extern void GsMulCoord2(void);
extern void GsMulCoord3(void);
extern void GsScanAnim(void);
extern void GsScanUnit(void);
extern void GsSetAmbient(void);
extern void GsSetFlatLight(void);
extern void GsSetLightMatrix(void);
extern void GsSetLsMatrix(void);
extern void GsSetOrign(void);
extern void GsSetProjection(void);
extern void GsSetRefView2(void);
extern void GsSetWorkBase(void);
extern void GsSortBoxFill(void);
extern void GsSortFastSprite(void);
extern void GsSortFlipSprite(void);
extern void GsSortGLine(void);
extern void GsSortLine(void);
extern void GsSortOt(void);
extern void GsSortPoly(void);
extern void GsSortSprite(void);
extern void GsSortUnit(void);
extern void GsSwapDispBuff(void);
extern void GsU_00000000(void);
extern void GsU_02000000(void);
extern void GsU_02000001(void);
extern void HostFile_GetSize(void);
extern void HostFile_ReadAll(void);
extern void HostFile_ReadRange(void);
extern void InitGeom(void);
extern void InitPAD(void);
extern void Input_BackupPad1AndUsePad2(void);
extern void Input_InitPads(void);
extern void Input_IsPad1ConfirmPressed(void);
extern void Input_ReadRawPads(void);
extern void Input_ResetPads(void);
extern void Input_RestorePad1FromBackup(void);
extern void Input_UpdatePads(void);
extern void IsIdleGPU(void);
extern void Krom2RawAdd(void);
extern void Krom2RawAdd2(void);
extern void Library_CheckCardOwned(void);
extern void Library_DrawCardGrid(void);
extern void Library_GetCardFlags(void);
extern void Library_GetGridCursorCardId(void);
extern void Library_MarkOwnedCards(void);
extern void Library_UpdateCardUsedFlag(void);
extern void Library_UpdateGridCursor(void);
extern void LoadImage(void);
extern void LoadImage2(void);
extern void MainMenu_AdjustTradeCardCount(void);
extern void MainMenu_ApplyTradeOfferInventoryDelta(void);
extern void MainMenu_CompareCardsByAttack(void);
extern void MainMenu_CompareCardsByCount(void);
extern void MainMenu_CompareCardsByDefense(void);
extern void MainMenu_CompareCardsByMaxStat(void);
extern void MainMenu_CompareCardsByName(void);
extern void MainMenu_CompareCardsByType(void);
extern void MainMenu_CountDecimalDigits(void);
extern void MainMenu_DestroyFrontendMenu(void);
extern void MainMenu_DrawCardTypeIcon(void);
extern void MainMenu_DrawFrontendBackground(void);
extern void MainMenu_DrawThreeDigitNumber(void);
extern void MainMenu_DrawTradeColumnOverlay(void);
extern void MainMenu_DrawTradeOffersAndHighlights(void);
extern void MainMenu_DrawValueSetup(void);
extern void MainMenu_FinishValueSetup(void);
extern void MainMenu_InitFrontendMenu(void);
extern void MainMenu_InitTradeScreen(void);
extern void MainMenu_LoadPackageStage(void);
extern void MainMenu_RebuildTradeInventoryRows(void);
extern void MainMenu_RefreshTradeInventory(void);
extern void MainMenu_ReleaseTradeDisplayHandles(void);
extern void MainMenu_SpawnFrontendEntryAfterimage(void);
extern void MainMenu_StartFrontendEntryTransition(void);
extern void MainMenu_StartValueSetup(void);
extern void MainMenu_StartValueWidgetTween(void);
extern void MainMenu_UpdateFrontendEntryAfterimage(void);
extern void MainMenu_UpdateFrontendMenu(void);
extern void MainMenu_UpdateTradeScreen(void);
extern void MainMenu_UpdateValueSetup(void);
extern void MainMenu_UpdateValueWidgetTween(void);
extern void Main_AdvanceFrame(void);
extern void Main_AdvanceFrames(void);
extern void Main_ApplyMenuSelection(void);
extern void Main_ClearFrameServiceCallbacks(void);
extern void Main_HoldBootScreen(void);
extern void Main_Init(void);
extern void Main_InitFreeDuelMenu(void);
extern void Main_LoadBootImageStage(void);
extern void Main_LoadBootPackageStage(void);
extern void Main_Loop(void);
extern void Main_PrepareFrontendLoop(void);
extern void Main_ResetFrontendRuntime(void);
extern void Main_RunAnimatedBattle(void);
extern void Main_RunBootSequence(void);
extern void Main_RunBuildDeckMenu(void);
extern void Main_RunCampaign(void);
extern void Main_RunCampaignMap(void);
extern void Main_RunCredits(void);
extern void Main_RunDebugMenu(void);
extern void Main_RunDuel(void);
extern void Main_RunFrameServices(void);
extern void Main_RunFreeDuelMenu(void);
extern void Main_RunFrontendLoop(void);
extern void Main_RunGameOver(void);
extern void Main_RunLibraryMenu(void);
extern void Main_RunMenu(void);
extern void Main_RunNameEntry(void);
extern void Main_RunOptionsMenu(void);
extern void Main_RunPasswordMenu(void);
extern void Main_RunTrade(void);
extern void Main_RunTwoPlayerDuelSetup(void);
extern void Main_RunUnusedDeveloperMode(void);
extern void Main_VBlankCB(void);
extern void MemCardAccept(void);
extern void MemCardCreateFile(void);
extern void MemCardDialog_CreateObject(void);
extern void MemCardDialog_Poll(void);
extern void MemCardDialog_Request(void);
extern void MemCardDialog_SetMessage(void);
extern void MemCardDialog_Start(void);
extern void MemCardDialog_StepLoad(void);
extern void MemCardDialog_StepLoadUnprompted(void);
extern void MemCardDialog_StepNone(void);
extern void MemCardDialog_StepSave(void);
extern void MemCardDialog_StepSlide(void);
extern void MemCardDialog_Update(void);
extern void MemCardDialog_UpdateLoad(void);
extern void MemCardDialog_UpdateSave(void);
extern void MemCardDialog_UpdateTradeSave(void);
extern void MemCardEnd(void);
extern void MemCardExist(void);
extern void MemCardFormat(void);
extern void MemCardGetDirentry(void);
extern void MemCardInit(void);
extern void MemCardReadFile(void);
extern void MemCardStart(void);
extern void MemCardStop(void);
extern void MemCardSync(void);
extern void MemCardWriteFile(void);
extern void MemCard_BeginRequest(void);
extern void MemCard_CalcFreeBlocks(void);
extern void MemCard_ClearCard(void);
extern void MemCard_ClearIOEvents(void);
extern void MemCard_CloseIOEvents(void);
extern void MemCard_DoLoadDirectory(void);
extern void MemCard_FindEntry(void);
extern void MemCard_FindFiles(void);
extern void MemCard_FindLoadedEntry(void);
extern void MemCard_Init(void);
extern void MemCard_InitIOEvents(void);
extern void MemCard_ProcessRequest(void);
extern void MemCard_ReqCardInfo(void);
extern void MemCard_ReqCreateFile(void);
extern void MemCard_ReqLoadDirectory(void);
extern void MemCard_ReqReadFile(void);
extern void MemCard_ReqReadSector(void);
extern void MemCard_ReqWriteFile(void);
extern void MemCard_ReqWriteSector(void);
extern void MemCard_SetIOResultCompleteCB(void);
extern void MemCard_SetIOResultErrorCB(void);
extern void MemCard_SetIOResultNewCardCB(void);
extern void MemCard_SetIOResultTimeoutCB(void);
extern void MemCard_WaitIOEvent(void);
extern void Memories_CreditsInit(void);
extern void Memories_CreditsLines(void);
extern void Memories_CreditsUpdate(void);
extern void Memories_DuelEffectControl(void);
extern void Memories_ModelPrimaryControlA(void);
extern void Memories_ModelPrimaryControlB(void);
extern void Memories_ModelVariantControlA(void);
extern void Memories_ModelVariantControlB(void);
extern void ModelDebug_UpdateController(void);
extern void ModelTexture_LoadTim(void);
extern void ModelTexture_PackPageClut(void);
extern void Model_ApplyTextureTint(void);
extern void Model_BuildCameraRelativeCoordinateUnit(void);
extern void Model_ControlSlotAnimation(void);
extern void Model_CopySlotU16Values(void);
extern void Model_CopyWords(void);
extern void Model_FillWords(void);
extern void Model_FindHandlerKey(void);
extern void Model_GetActiveSlotIndex(void);
extern void Model_GetCameraCoordinateUnit(void);
extern void Model_GetCameraViewBuffer(void);
extern void Model_GetCurrentDataEntry(void);
extern void Model_GetFlatLight(void);
extern void Model_GetFrameStep(void);
extern void Model_GetLightSourceMatrix(void);
extern void Model_GetPrimitiveHandler(void);
extern void Model_GetSlotAnimationFrame(void);
extern void Model_GetSlotAnimationIndex(void);
extern void Model_GetSlotAnimationLength(void);
extern void Model_GetSlotAnimationSpeed(void);
extern void Model_GetSlotDataEntry(void);
extern void Model_GetSlotDistanceFromCameraEye(void);
extern void Model_GetSlotDistanceFromCameraTarget(void);
extern void Model_GetViewMetricsBuffer(void);
extern void Model_HasInsufficientBufferSpace(void);
extern void Model_InitLightTriplet(void);
extern void Model_IsCreditsPresentationComplete(void);
extern void Model_IsExodiaPresentationComplete(void);
extern void Model_LoadMonsterMerge(void);
extern void Model_ProcessType2Unit(void);
extern void Model_QueueTintRequest(void);
extern void Model_QueueTintRequestForParts(void);
extern void Model_RegisterHandlerKey(void);
extern void Model_RunSlotHandlers(void);
extern void Model_SetCameraEyeSlots(void);
extern void Model_SetFrameStepOverride(void);
extern void Model_SetPresentationBgmCommand(void);
extern void Model_SetScreenYOverride(void);
extern void Model_SetSlotProperties(void);
extern void Model_SetSlotShadowEnabled(void);
extern void Model_SetSlotTintTarget(void);
extern void Model_StartCreditsPresentation(void);
extern void Model_StartExodiaPresentation(void);
extern void Model_UpdateDiscEffect(void);
extern void Model_UpdateScene(void);
extern void Model_UpdateViewMetrics(void);
extern void MoveImage(void);
extern void MoveImage2(void);
extern void Movie_DecodeAndPresentFrame(void);
extern void Movie_MoveDisplayImage(void);
extern void Movie_Play(void);
extern void Movie_ResetPlaybackState(void);
extern void Movie_StartFadeOut(void);
extern void Movie_StartFileStream(void);
extern void Movie_StepPlayback(void);
extern void Movie_StopStream(void);
extern void Movie_WaitAndDecodeFrame(void);
extern void Movie_WaitFrameDecoded(void);
extern void MulMatrix(void);
extern void MulMatrix0(void);
extern void MulMatrix2(void);
extern void NameEntry_AdjustLength(void);
extern void NameEntry_BuildKeyboardTextBox(void);
extern void NameEntry_BuildStarterDeck(void);
extern void NameEntry_DrawSelectionFrame(void);
extern void NameEntry_Init(void);
extern void NameEntry_LoadPackageStage(void);
extern void NameEntry_Main(void);
extern void NameEntry_PollCompletion(void);
extern void NameEntry_SpawnGlyphSprite(void);
extern void NameEntry_UpdateCaretTween(void);
extern void NameEntry_UpdateDialog(void);
extern void NameEntry_UpdateGlyphFragment(void);
extern void NameEntry_UpdateGlyphPulse(void);
extern void NameEntry_UpdateGlyphShatter(void);
extern void NameEntry_UpdateGlyphTransfer(void);
extern void NameEntry_UpdateKeyboard(void);
extern void NormalClip(void);
extern void NormalColorCol(void);
extern void OpenEvent(void);
extern void Options_HandleInput(void);
extern void Options_Init(void);
extern void Options_InitTextDisplay(void);
extern void Options_LoadPackageStage(void);
extern void Options_Update(void);
extern void Options_UpdateLayout(void);
extern void Password_CreateMessageBox(void);
extern void Password_InitShopScreen(void);
extern void Password_LoadPackageStage(void);
extern void Password_LookupCardID(void);
extern void Password_RecreateCardPreview(void);
extern void Password_RefreshDigitDisplay(void);
extern void Password_RefreshStarchipDisplay(void);
extern void Password_SetDigitCursorTarget(void);
extern void Password_UpdateDigitCursor(void);
extern void Password_UpdateDigitCursorDecoration(void);
extern void Password_UpdateShopScreen(void);
extern void PopMatrix(void);
extern void PushMatrix(void);
extern void PutDispEnv(void);
extern void PutDrawEnv(void);
extern void Rand_GetInterval(void);
extern void ReadGeomScreen(void);
extern void ReadRotMatrix(void);
extern void ResetCallback(void);
extern void ResetGraph(void);
extern void RotAverage3(void);
extern void RotAverage4(void);
extern void RotAverageNclip3(void);
extern void RotAverageNclip3_nom(void);
extern void RotAverageNclip4(void);
extern void RotColorDpq(void);
extern void RotMatrix(void);
extern void RotMatrixX(void);
extern void RotMatrixY(void);
extern void RotMatrixYXZ(void);
extern void RotMatrixYXZ_gte(void);
extern void RotMatrixZ(void);
extern void RotMatrixZXY(void);
extern void RotMatrixZYX(void);
extern void RotMatrixZYX_gte(void);
extern void RotMatrix_gte(void);
extern void RotTrans(void);
extern void RotTransPers(void);
extern void RotTransPers3(void);
extern void RotTransPers4(void);
extern void RotTransPersN(void);
extern void RotTransSV(void);
extern void SD_AdvanceSequencePosition(void);
extern void SD_ApplyPositionalSound(void);
extern void SD_ApplyVoiceSlotVolume(void);
extern void SD_ArmBusyCallback(void);
extern void SD_BGMFadeOut(void);
extern void SD_BGMFadeOutWithStep(void);
extern void SD_BGMPlay(void);
extern void SD_CalcPitchBend(void);
extern void SD_CalcSpatialVolumePan(void);
extern void SD_ClearBusyFlag(void);
extern void SD_CloseSequenceTimerEvent(void);
extern void SD_CompareBytes(void);
extern void SD_ConfigureTransferPhase(void);
extern void SD_DisableSecondaryPanning(void);
extern void SD_DispatchSequenceChannelEvent(void);
extern void SD_EnableSecondaryPanning(void);
extern void SD_EnableSecondarySequenceUpdates(void);
extern void SD_EnqueueCommand(void);
extern void SD_FindLowestPrioritySecondaryObject(void);
extern void SD_FindMidiTrackChunk(void);
extern void SD_GetCdVolume(void);
extern void SD_GetOutputType(void);
extern void SD_GetSequenceStatus(void);
extern void SD_GetStatusFlags(void);
extern void SD_HandleSequenceMetaEvent(void);
extern void SD_HasQueuedStreamCommand(void);
extern void SD_IgnoreSequenceEvent(void);
extern void SD_Init(void);
extern void SD_InitBufferState(void);
extern void SD_InitDataSourceFlags(void);
extern void SD_InitSecondaryRuntime(void);
extern void SD_InitSecondaryWorkArea(void);
extern void SD_InitState(void);
extern void SD_InitVoiceState(void);
extern void SD_IsBgmFadeActive(void);
extern void SD_KeyOffVoice(void);
extern void SD_KeyOffVoiceSlots(void);
extern void SD_LoadSequenceBankPair(void);
extern void SD_MuteSecondaryVoices(void);
extern void SD_OpenMusicVab(void);
extern void SD_OpenSequence(void);
extern void SD_OpenSequenceTimerEvent(void);
extern void SD_OpenSequenceTrack(void);
extern void SD_PlaySequence(void);
extern void SD_PlaySequenceFastForward(void);
extern void SD_PollSequenceState(void);
extern void SD_PrepareSecondaryObjectReuse(void);
extern void SD_ProcessSequenceTracks(void);
extern void SD_QueueValueLinkTransfer(void);
extern void SD_ReadSequenceByte(void);
extern void SD_ReadSequenceEvent(void);
extern void SD_ReadSequenceHeader(void);
extern void SD_ReadSequenceU16BE(void);
extern void SD_ReadSequenceU32BE(void);
extern void SD_ReadVariableLengthValue(void);
extern void SD_RequestBgmPlayback(void);
extern void SD_RequestBgmPlaybackDefaultStep(void);
extern void SD_RequestMusicPackageLoad(void);
extern void SD_RequestValueLink(void);
extern void SD_ResetCdPan(void);
extern void SD_ResetMusicState(void);
extern void SD_ResetMusicTrackBuffer(void);
extern void SD_ResetRuntime(void);
extern void SD_ResetSecondaryPlayback(void);
extern void SD_ResetSecondaryRuntime(void);
extern void SD_ResetSecondaryState(void);
extern void SD_ResetSequenceTracks(void);
extern void SD_ResetVabTransferState(void);
extern void SD_ResetVoiceEnvelope(void);
extern void SD_RestoreSecondaryVoiceVolumes(void);
extern void SD_SEPlay(void);
extern void SD_SEPlayFull(void);
extern void SD_SESetVolume(void);
extern void SD_SEStop(void);
extern void SD_ScaleSequenceDelta(void);
extern void SD_SelectSecondaryObject(void);
extern void SD_SequenceTimerCallback(void);
extern void SD_SetCdPan(void);
extern void SD_SetMusicTrackBuffer(void);
extern void SD_SetOutputType(void);
extern void SD_SetSecondaryMasterLevels(void);
extern void SD_SetSecondaryObjectCount(void);
extern void SD_SetSecondarySpatialLevels(void);
extern void SD_SetSequenceChannelProgram(void);
extern void SD_SetSequenceTickMode(void);
extern void SD_SetSequenceVSyncMode(void);
extern void SD_SetVoiceEnvelopeFromTone(void);
extern void SD_SetVoiceVolume(void);
extern void SD_Shutdown(void);
extern void SD_SkipSequenceSysEx(void);
extern void SD_SpatializeSecondaryObject(void);
extern void SD_StartSequenceTracks(void);
extern void SD_StopAll(void);
extern void SD_StopSequence(void);
extern void SD_StopSequenceTimer(void);
extern void SD_Term(void);
extern void SD_UpdateFades(void);
extern void SD_UpdateRuntime(void);
extern void SD_UpdateSecondaryObjectVolumes(void);
extern void SD_UpdateSecondarySequence(void);
extern void SD_UpdateSecondarySequenceIfEnabled(void);
extern void SD_UpdateVoiceSlots(void);
extern void SD_VSync(void);
extern void SD_VabOpenHead(void);
extern void SD_VabTransBody(void);
extern void SD_VabTransBodyChunk(void);
extern void SD_VabTransCompleted(void);
extern void SaveData_ApplyRuntimeState(void);
extern void SaveData_BuildPayload(void);
extern void SaveData_CalcCrc16(void);
extern void SaveData_HasSameDuelistCode(void);
extern void SaveData_MatchesDuelistAndCurrentSequence(void);
extern void SaveData_NextMaskWord(void);
extern void SaveData_PollLoad(void);
extern void SaveData_RequestLoad(void);
extern void SaveData_RequestTradeWrite(void);
extern void SaveData_RequestWrite(void);
extern void SaveData_SetMaskSeed(void);
extern void SaveData_UpdateDuelLoad(void);
extern void SaveData_UpdateLoadPair(void);
extern void SaveData_UpdateTradeLoad(void);
extern void SaveData_ValidateIntegrity(void);
extern void SaveData_WritePrimarySecondaryIntegrity(void);
extern void SaveData_WriteTertiaryIntegrity(void);
extern void ScaleMatrix(void);
extern void SceneScript_NoOpRecordCallback(void);
extern void SceneScript_UpdateSlots(void);
extern void ScriptCommand_MarkStarted(void);
extern void ScriptImage_CreateObject(void);
extern void ScriptImage_RebuildObjects(void);
extern void ScriptImage_ReleaseObjects(void);
extern void ScriptImage_RequestTransfer(void);
extern void ScriptImage_TransferCallback(void);
extern void Script_OpCredits(void);
extern void Script_OpDuelResult(void);
extern void Script_OpFadeBgm(void);
extern void Script_OpFadeOut(void);
extern void Script_OpGameOver(void);
extern void Script_OpHalt(void);
extern void Script_OpJump(void);
extern void Script_OpJumpIfDeckIncomplete(void);
extern void Script_OpLoadImageScene(void);
extern void Script_OpOpenCampaignMap(void);
extern void Script_OpReturnToMenu(void);
extern void Script_OpSavePrompt(void);
extern void Script_OpShowDialog(void);
extern void Script_OpShowImage(void);
extern void Script_OpShowMenu(void);
extern void Script_OpSound(void);
extern void Script_OpStageImage(void);
extern void Script_OpStoryFlag(void);
extern void Script_OpUnusedHalt14(void);
extern void Script_OpUnusedHalt15(void);
extern void Script_OpViewportTween(void);
extern void Script_OpWait(void);
extern void Script_ReadByte(void);
extern void Script_ReadU16LE(void);
extern void Script_RunTick(void);
extern void Script_UpdateViewportTween(void);
extern void SetBackColor(void);
extern void SetColorMatrix(void);
extern void SetDispMask(void);
extern void SetDumpFnt(void);
extern void SetFarColor(void);
extern void SetFogNearFar(void);
extern void SetGeomOffset(void);
extern void SetGeomScreen(void);
extern void SetLightMatrix(void);
extern void SetMem(void);
extern void SetPolyF3(void);
extern void SetPolyF4(void);
extern void SetPolyFT3(void);
extern void SetPolyFT4(void);
extern void SetPolyG3(void);
extern void SetPolyG4(void);
extern void SetPolyGT3(void);
extern void SetPolyGT4(void);
extern void SetRCnt(void);
extern void SetRotMatrix(void);
extern void SetSemiTrans(void);
extern void SetShadeTex(void);
extern void SetTransMatrix(void);
extern void SortedEntry_BeginCollection(void);
extern void SortedEntry_Compare(void);
extern void SortedEntry_SortAndRelink(void);
extern void Sound_InitFrontend(void);
extern void SpuGetAllKeysStatus(void);
extern void SpuGetKeyStatus(void);
extern void SpuGetReverb(void);
extern void SpuGetReverbVoice(void);
extern void SpuGetVoiceEnvelope(void);
extern void SpuInit(void);
extern void SpuIsReverbWorkAreaReserved(void);
extern void SpuIsTransferCompleted(void);
extern void SpuQuit(void);
extern void SpuReadDecodedData(void);
extern void SpuReserveReverbWorkArea(void);
extern void SpuSetCommonAttr(void);
extern void SpuSetIRQ(void);
extern void SpuSetKey(void);
extern void SpuSetKeyOnWithAttr(void);
extern void SpuSetReverb(void);
extern void SpuSetReverbModeParam(void);
extern void SpuSetReverbModeType(void);
extern void SpuSetReverbVoice(void);
extern void SpuSetTransferMode(void);
extern void SpuSetTransferStartAddr(void);
extern void SpuSetVoiceAttr(void);
extern void SpuWrite(void);
extern void Square0(void);
extern void SquareRoot0(void);
extern void StCdInterrupt(void);
extern void StClearRing(void);
extern void StFreeRing(void);
extern void StGetBackloc(void);
extern void StGetNext(void);
extern void StSetRing(void);
extern void StSetStream(void);
extern void StUnSetRing(void);
extern void StartPAD(void);
extern void StartRCnt(void);
extern void StopCallback(void);
extern void StopRCnt(void);
extern void StoreImage(void);
extern void StoreImage2(void);
extern void TestEvent(void);
extern void TextBox_BuildStep(void);
extern void TextBox_Create(void);
extern void TextBox_CreateFlagged(void);
extern void TextBox_Destroy(void);
extern void TextBox_GetGlyphAt(void);
extern void TextBox_SetPos(void);
extern void TextBox_SetRect(void);
extern void TextBox_WaitForScriptCompletion(void);
extern void TextBox_WrapLineIfNeeded(void);
extern void TextStream_ReadByte(void);
extern void TextStream_ReadU16LE(void);
extern void TextStream_ReadU32LE(void);
extern void Text_ApplyFadeCommand(void);
extern void Text_CloseChoice(void);
extern void Text_CompletePageAdvance(void);
extern void Text_DispatchSecondaryCommand(void);
extern void Text_EncodeDecimalDigits(void);
extern void Text_EncodeDecimalNoPadding(void);
extern void Text_EndStream(void);
extern void Text_ExtendGlyphCode(void);
extern void Text_FindRecordById(void);
extern void Text_HandleCampaignFlagCommand(void);
extern void Text_HandleChoiceCommand(void);
extern void Text_HandleDisplayEffectCommand(void);
extern void Text_InitDecimalDigitGlyphMap(void);
extern void Text_LookupString(void);
extern void Text_NewLine(void);
extern void Text_PushStreamOffset(void);
extern void Text_SetCursorOffset(void);
extern void Text_SetStateFromStream(void);
extern void Text_SjisToGlyphCodes(void);
extern void Text_StartCampaignDuel(void);
extern void Text_StartPageWait(void);
extern void Text_TryCompleteChoiceLayout(void);
extern void Text_UnlockDuelist(void);
extern void TransMatrix(void);
extern void TransposeMatrix(void);
extern void Triplet_SetComponents(void);
extern void Util_CompareS16(void);
extern void Util_CopyWords(void);
extern void Util_FillMemory(void);
extern void VSync(void);
extern void VSyncCallback(void);
extern void ViewState_ApplyOrbit(void);
extern void ViewState_ApplyViewpointOffset(void);
extern void Widget_SlideSine(void);
extern void Widget_UpdatePulseColour(void);
extern void bzero(void);
extern void catan(void);
extern void func_80013154(void);
extern void func_80013360(void);
extern void func_800135FC(void);
extern void func_800136D4(void);
extern void func_80013A94(void);
extern void func_800140A0(void);
extern void func_80014134(void);
extern void func_800141A8(void);
extern void func_80014220(void);
extern void func_80014294(void);
extern void func_80014308(void);
extern void func_80014390(void);
extern void func_800144B8(void);
extern void func_80014C40(void);
extern void func_80014FA4(void);
extern void func_80015010(void);
extern void func_80015038(void);
extern void func_8001513C(void);
extern void func_800156DC(void);
extern void func_8001572C(void);
extern void func_80015870(void);
extern void func_80015A50(void);
extern void func_80015A94(void);
extern void func_80015B50(void);
extern void func_80015B94(void);
extern void func_80015D18(void);
extern void func_80015DB8(void);
extern void func_80015DFC(void);
extern void func_80015EF4(void);
extern void func_80016784(void);
extern void func_80016D2C(void);
extern void func_80017130(void);
extern void func_800177C4(void);
extern void func_800178BC(void);
extern void func_80017DB4(void);
extern void func_80017E3C(void);
extern void func_80017F04(void);
extern void func_80018004(void);
extern void func_80018150(void);
extern void func_80019BA0(void);
extern void func_80019BD0(void);
extern void func_80019CC8(void);
extern void func_8001B0CC(void);
extern void func_8001B170(void);
extern void func_8001B780(void);
extern void func_8001B7AC(void);
extern void func_8001B8B8(void);
extern void func_8001B938(void);
extern void func_8001BAF0(void);
extern void func_8001D344(void);
extern void func_8001D3C4(void);
extern void func_8001D518(void);
extern void func_8001D5B4(void);
extern void func_8001EC70(void);
extern void func_8001ED20(void);
extern void func_8001EFD4(void);
extern void func_80020988(void);
extern void func_80020BE4(void);
extern void func_80020EE8(void);
extern void func_800220B8(void);
extern void func_800222F4(void);
extern void func_80022674(void);
extern void func_800229F4(void);
extern void func_80022D94(void);
extern void func_80023090(void);
extern void func_80023144(void);
extern void func_8002348C(void);
extern void func_800234E4(void);
extern void func_800235C0(void);
extern void func_80023D08(void);
extern void func_80023FBC(void);
extern void func_80024060(void);
extern void func_80024088(void);
extern void func_80024C1C(void);
extern void func_80024D34(void);
extern void func_80024DC8(void);
extern void func_8002712C(void);
extern void func_80027228(void);
extern void func_80027508(void);
extern void func_8002778C(void);
extern void func_800278A0(void);
extern void func_800279BC(void);
extern void func_80027DF8(void);
extern void func_80028220(void);
extern void func_8002827C(void);
extern void func_800283EC(void);
extern void func_800289AC(void);
extern void func_800289B4(void);
extern void func_800289BC(void);
extern void func_80028B08(void);
extern void func_80029164(void);
extern void func_800291E0(void);
extern void func_80029528(void);
extern void func_80029590(void);
extern void func_80029684(void);
extern void func_800297DC(void);
extern void func_80029934(void);
extern void func_8002A2F4(void);
extern void func_8002A3CC(void);
extern void func_8002A4A8(void);
extern void func_8002A660(void);
extern void func_8002A9C0(void);
extern void func_8002ABB4(void);
extern void func_8002ACA4(void);
extern void func_8002BAA0(void);
extern void func_8002BAAC(void);
extern void func_8002BAB4(void);
extern void func_8002BD0C(void);
extern void func_8002BFCC(void);
extern void func_8002C400(void);
extern void func_8002C484(void);
extern void func_8002C560(void);
extern void func_8002C568(void);
extern void func_8002C570(void);
extern void func_8002F4C0(void);
extern void func_8002FED8(void);
extern void func_80030250(void);
extern void func_80030294(void);
extern void func_80030C10(void);
extern void func_8003134C(void);
extern void func_800313E8(void);
extern void func_80031574(void);
extern void func_800316F0(void);
extern void func_80031874(void);
extern void func_80031E04(void);
extern void func_8003201C(void);
extern void func_80032184(void);
extern void func_80032328(void);
extern void func_80032370(void);
extern void func_800323F8(void);
extern void func_80032BD4(void);
extern void func_80032C48(void);
extern void func_800339D0(void);
extern void func_80033BE8(void);
extern void func_80033CF8(void);
extern void func_80033DB0(void);
extern void func_80034830(void);
extern void func_80035668(void);
extern void func_800359B0(void);
extern void func_80035A64(void);
extern void func_80035CA8(void);
extern void func_80035D10(void);
extern void func_80035E20(void);
extern void func_800373C8(void);
extern void func_800374A8(void);
extern void func_800375A4(void);
extern void func_8003767C(void);
extern void func_8003771C(void);
extern void func_800377C8(void);
extern void func_8003787C(void);
extern void func_800378D8(void);
extern void func_80037914(void);
extern void func_80037950(void);
extern void func_8003798C(void);
extern void func_800379C4(void);
extern void func_800379F8(void);
extern void func_80037A58(void);
extern void func_80037B40(void);
extern void func_80037DA4(void);
extern void func_80038024(void);
extern void func_80038070(void);
extern void func_80038094(void);
extern void func_800380D4(void);
extern void func_80038110(void);
extern void func_80038148(void);
extern void func_800382A8(void);
extern void func_80038334(void);
extern void func_80038388(void);
extern void func_800383B0(void);
extern void func_800383DC(void);
extern void func_80038498(void);
extern void func_800384E4(void);
extern void func_80038888(void);
extern void func_80038890(void);
extern void func_80038898(void);
extern void func_800389C4(void);
extern void func_800389D8(void);
extern void func_80038A44(void);
extern void func_80039140(void);
extern void func_800391E4(void);
extern void func_80039794(void);
extern void func_80039A14(void);
extern void func_80039A60(void);
extern void func_80039AFC(void);
extern void func_80039BE0(void);
extern void func_80039C94(void);
extern void func_80039E9C(void);
extern void func_80039F1C(void);
extern void func_80039F44(void);
extern void func_80039F90(void);
extern void func_80039FD4(void);
extern void func_80039FF8(void);
extern void func_8003A440(void);
extern void func_8003A560(void);
extern void func_8003A920(void);
extern void func_8003A990(void);
extern void func_8003AAE4(void);
extern void func_8003AC48(void);
extern void func_8003AD6C(void);
extern void func_8003B054(void);
extern void func_8003CA5C(void);
extern void func_8003D300(void);
extern void func_8003D32C(void);
extern void func_8003D518(void);
extern void func_8003D614(void);
extern void func_8003D74C(void);
extern void func_8003DA40(void);
extern void func_8003DC1C(void);
extern void func_8003FF88(void);
extern void func_8003FFB4(void);
extern void func_8003FFD8(void);
extern void func_80041E7C(void);
extern void func_80041F90(void);
extern void func_8004365C(void);
extern void func_80044DC0(void);
extern void func_80044F58(void);
extern void func_80044FFC(void);
extern void func_8004503C(void);
extern void func_80045054(void);
extern void func_80045114(void);
extern void func_800451E0(void);
extern void func_80045208(void);
extern void func_80045334(void);
extern void func_80045514(void);
extern void func_80046294(void);
extern void func_800464F0(void);
extern void func_8004666C(void);
extern void func_800466C8(void);
extern void func_8004671C(void);
extern void func_80046A08(void);
extern void func_8004701C(void);
extern void func_800470B0(void);
extern void func_80047140(void);
extern void func_800471D0(void);
extern void func_80047278(void);
extern void func_800472A8(void);
extern void func_80047314(void);
extern void func_8004733C(void);
extern void func_800473CC(void);
extern void func_800473F0(void);
extern void func_80047430(void);
extern void func_80047458(void);
extern void func_8004763C(void);
extern void func_800476B4(void);
extern void func_80047A68(void);
extern void func_80047AD0(void);
extern void func_80047BB4(void);
extern void func_80047C50(void);
extern void func_80047CC4(void);
extern void func_80047F38(void);
extern void func_80047FAC(void);
extern void func_8004803C(void);
extern void func_800482B0(void);
extern void func_80048768(void);
extern void func_80048A28(void);
extern void func_80048C0C(void);
extern void func_80048C70(void);
extern void func_800490F0(void);
extern void func_80049108(void);
extern void func_80049920(void);
extern void func_80049CB0(void);
extern void func_80049FB4(void);
extern void func_8004A43C(void);
extern void func_8004A6D8(void);
extern void func_8004A7C0(void);
extern void func_8004AAFC(void);
extern void func_8004ACE4(void);
extern void func_8004ADE8(void);
extern void func_8004B374(void);
extern void func_8004B49C(void);
extern void func_8004B70C(void);
extern void func_8004C84C(void);
extern void func_8004CB0C(void);
extern void func_8004D134(void);
extern void func_8004D58C(void);
extern void func_8004D75C(void);
extern void func_8004D914(void);
extern void func_8004DB14(void);
extern void func_8004DC38(void);
extern void func_8004DE24(void);
extern void func_8004E7B0(void);
extern void func_8004E9A0(void);
extern void func_8004EB00(void);
extern void func_8004FE2C(void);
extern void func_80050584(void);
extern void func_800507D0(void);
extern void func_80050F24(void);
extern void func_8005106C(void);
extern void func_80051350(void);
extern void func_80051A48(void);
extern void func_80052528(void);
extern void func_80052694(void);
extern void func_800528AC(void);
extern void func_80052D2C(void);
extern void func_800530C4(void);
extern void func_800533D8(void);
extern void func_800540B4(void);
extern void func_800556E8(void);
extern void func_800559D4(void);
extern void func_8005611C(void);
extern void func_80056250(void);
extern void func_80056828(void);
extern void func_80056D7C(void);
extern void func_80057544(void);
extern void func_800577B0(void);
extern void func_80057E20(void);
extern void func_800580D4(void);
extern void func_80058434(void);
extern void func_80058DC0(void);
extern void func_80058DD8(void);
extern void func_80058F10(void);
extern void func_80059000(void);
extern void func_800590DC(void);
extern void func_8005922C(void);
extern void func_80059284(void);
extern void func_800593D0(void);
extern void func_8005949C(void);
extern void func_800594C0(void);
extern void func_80059520(void);
extern void func_800595C8(void);
extern void func_8005969C(void);
extern void func_80059700(void);
extern void func_800597C8(void);
extern void func_800599FC(void);
extern void func_80059A50(void);
extern void func_80059AF8(void);
extern void func_80059B90(void);
extern void func_80059EBC(void);
extern void func_80059F18(void);
extern void func_8005A010(void);
extern void func_8005A074(void);
extern void func_8005A0DC(void);
extern void func_8005A130(void);
extern void func_8005A188(void);
extern void func_8005A3D0(void);
extern void func_8005A468(void);
extern void func_8005A4C4(void);
extern void func_8005A53C(void);
extern void func_8005A618(void);
extern void func_8005A878(void);
extern void func_8005B054(void);
extern void func_8005B0B4(void);
extern void func_8005B260(void);
extern void func_8005B4D8(void);
extern void func_8005B8A0(void);
extern void func_8005C1F4(void);
extern void func_8005C374(void);
extern void func_8005C388(void);
extern void func_8005C62C(void);
extern void func_8005C690(void);
extern void func_8005C6A0(void);
extern void func_8005C768(void);
extern void func_8005C7BC(void);
extern void func_8005CEF0(void);
extern void func_8005D378(void);
extern void func_8005D994(void);
extern void func_8005DBA4(void);
extern void func_8005E808(void);
extern void func_8005EBF4(void);
extern void func_8005F070(void);
extern void func_8005F174(void);
extern void func_8005F180(void);
extern void func_8005F18C(void);
extern void func_8005F198(void);
extern void func_8005F1A4(void);
extern void func_8005F1B8(void);
extern void func_8005F27C(void);
extern void func_8005F3B8(void);
extern void func_8005F564(void);
extern void func_8005F588(void);
extern void func_8005F5C8(void);
extern void func_8005F714(void);
extern void func_8005F7B0(void);
extern void func_8005F828(void);
extern void func_8005F91C(void);
extern void func_8005FAE4(void);
extern void func_8005FB08(void);
extern void func_8005FB14(void);
extern void func_8005FB30(void);
extern void func_8005FBC4(void);
extern void func_8005FC1C(void);
extern void func_8005FE44(void);
extern void func_800603DC(void);
extern void func_8006086C(void);
extern void func_800608B8(void);
extern void func_80060AEC(void);
extern void func_80060E70(void);
extern void func_80061008(void);
extern void func_800610E0(void);
extern void func_800611D0(void);
extern void func_800612C0(void);
extern void func_8006151C(void);
extern void func_800617E0(void);
extern void func_80061A84(void);
extern void func_80061DDC(void);
extern void func_80062058(void);
extern void func_8006233C(void);
extern void func_80062600(void);
extern void func_80062978(void);
extern void func_80062BC0(void);
extern void func_80062E70(void);
extern void func_80063100(void);
extern void func_80063444(void);
extern void func_800636AC(void);
extern void func_8006397C(void);
extern void func_80063C2C(void);
extern void func_80063F90(void);
extern void func_80064248(void);
extern void func_80064568(void);
extern void func_80064868(void);
extern void func_80064C1C(void);
extern void func_80064EF4(void);
extern void func_80065234(void);
extern void func_80065554(void);
extern void func_80065928(void);
extern void func_80065BCC(void);
extern void func_80065ED8(void);
extern void func_800661C4(void);
extern void func_80066564(void);
extern void func_80066828(void);
extern void func_80066B54(void);
extern void func_80066E60(void);
extern void func_80067220(void);
extern void func_80067354(void);
extern void func_8006759C(void);
extern void func_80067858(void);
extern void func_80067ABC(void);
extern void func_80067D94(void);
extern void func_80067FD0(void);
extern void func_8006825C(void);
extern void func_800684B4(void);
extern void func_8006875C(void);
extern void func_80068A00(void);
extern void func_80068D18(void);
extern void func_80068FD8(void);
extern void func_8006930C(void);
extern void func_800695A4(void);
extern void func_8006988C(void);
extern void func_80069B40(void);
extern void func_80069E44(void);
extern void func_80069F94(void);
extern void func_8006A0E8(void);
extern void func_8006A268(void);
extern void func_8006A3F0(void);
extern void func_8006A540(void);
extern void func_8006A694(void);
extern void func_8006A814(void);
extern void func_8006A99C(void);
extern void func_8006AAFC(void);
extern void func_8006AC88(void);
extern void func_8006ADE8(void);
extern void func_8006AF74(void);
extern void func_8006BCA4(void);
extern void func_8006C120(void);
extern void func_8006C30C(void);
extern void func_8006C330(void);
extern void func_8006CD78(void);
extern void func_8006F1B4(void);
extern void func_80073464(void);
extern void func_80073474(void);
extern void func_801680B4(void);
extern void gteMIMefunc(void);
extern void ratan2(void);
extern void rcos(void);
extern void rsin(void);
const MemoriesGuestFunction Memories_FunctionMap[] = {
    {0x80012B50u, Main_Init, 0x00000000u, 0x0u},
    {0x80012CD4u, Main_VBlankCB, 0x00000000u, 0x0u},
    {0x80012D4Cu, Main_AdvanceFrame, 0x00000000u, 0x0u},
    {0x80012D84u, Main_AdvanceFrames, 0x00000000u, 0x0u},
    {0x80012DB4u, Graphics_SyncFrame, 0x00000000u, 0x0u},
    {0x80012E5Cu, Graphics_BeginFrame, 0x00000000u, 0x0u},
    {0x8001306Cu, Main_RunFrameServices, 0x00000000u, 0x0u},
    {0x80013154u, func_80013154, 0x00000000u, 0x0u},
    {0x80013360u, func_80013360, 0x00000000u, 0x0u},
    {0x800134B4u, Main_ClearFrameServiceCallbacks, 0x00000000u, 0x0u},
    {0x800134E0u, ViewState_ApplyViewpointOffset, 0x00000000u, 0x0u},
    {0x8001352Cu, ViewState_ApplyOrbit, 0x00000000u, 0x0u},
    {0x800135FCu, func_800135FC, 0x00000000u, 0x0u},
    {0x800136D4u, func_800136D4, 0x00000000u, 0x0u},
    {0x800136E4u, File_SetPositionTable, 0x00000000u, 0x0u},
    {0x800137E4u, File_WaitForTransfers, 0x00000000u, 0x0u},
    {0x80013898u, File_InitTransferState, 0x00000000u, 0x0u},
    {0x800138F4u, File_GetPosition, 0x00000000u, 0x0u},
    {0x80013940u, File_SetTransferLocation, 0x00000000u, 0x0u},
    {0x80013998u, File_InitTransferDescriptor, 0x00000000u, 0x0u},
    {0x80013A94u, func_80013A94, 0x00000000u, 0x0u},
    {0x80013B04u, File_TryStartPrimaryTransfer, 0x00000000u, 0x0u},
    {0x80013B68u, File_RequestSecondaryRangeTransfer, 0x00000000u, 0x0u},
    {0x80013C28u, File_TransferReadyCallback, 0x00000000u, 0x0u},
    {0x800140A0u, func_800140A0, 0x00000000u, 0x0u},
    {0x80014134u, func_80014134, 0x00000000u, 0x0u},
    {0x800141A8u, func_800141A8, 0x00000000u, 0x0u},
    {0x80014220u, func_80014220, 0x00000000u, 0x0u},
    {0x80014294u, func_80014294, 0x00000000u, 0x0u},
    {0x80014308u, func_80014308, 0x00000000u, 0x0u},
    {0x80014390u, func_80014390, 0x00000000u, 0x0u},
    {0x800143DCu, File_ActivateTransfer, 0x00000000u, 0x0u},
    {0x800144B8u, func_800144B8, 0x00000000u, 0x0u},
    {0x8001455Cu, File_StepActiveTransfer, 0x00000000u, 0x0u},
    {0x80014A5Cu, File_ServiceTransfers, 0x00000000u, 0x0u},
    {0x80014B30u, SD_ConfigureTransferPhase, 0x00000000u, 0x0u},
    {0x80014C40u, func_80014C40, 0x00000000u, 0x0u},
    {0x80014E1Cu, File_RequestAsyncTransfer, 0x00000000u, 0x0u},
    {0x80014EECu, File_TryRequestAsyncTransfer, 0x00000000u, 0x0u},
    {0x80014FA4u, func_80014FA4, 0x00000000u, 0x0u},
    {0x80015010u, func_80015010, 0x00000000u, 0x0u},
    {0x80015038u, func_80015038, 0x00000000u, 0x0u},
    {0x80015078u, File_RequestSecondaryAsyncTransfer, 0x00000000u, 0x0u},
    {0x8001513Cu, func_8001513C, 0x00000000u, 0x0u},
    {0x800151B0u, Fade_Init, 0x00000000u, 0x0u},
    {0x800151D8u, Fade_StepBands, 0x00000000u, 0x0u},
    {0x80015310u, Fade_Update, 0x00000000u, 0x0u},
    {0x800154E4u, Fade_DrawOverlay, 0x00000000u, 0x0u},
    {0x800156B8u, Fade_FillBandLevels, 0x00000000u, 0x0u},
    {0x800156DCu, func_800156DC, 0x00000000u, 0x0u},
    {0x8001572Cu, func_8001572C, 0x00000000u, 0x0u},
    {0x80015780u, Fade_InitIn, 0x00000000u, 0x0u},
    {0x800157DCu, Fade_StartIn, 0x00000000u, 0x0u},
    {0x8001581Cu, Fade_InitInColor, 0x00000000u, 0x0u},
    {0x80015870u, func_80015870, 0x00000000u, 0x0u},
    {0x800158B8u, Fade_InitOut, 0x00000000u, 0x0u},
    {0x80015904u, Fade_StartOut, 0x00000000u, 0x0u},
    {0x80015944u, Fade_InitOutColor, 0x00000000u, 0x0u},
    {0x80015998u, Fade_Wait, 0x00000000u, 0x0u},
    {0x800159D8u, Fade_WaitInitIn, 0x00000000u, 0x0u},
    {0x80015A00u, Fade_WaitIn, 0x00000000u, 0x0u},
    {0x80015A28u, Fade_WaitInitInColor, 0x00000000u, 0x0u},
    {0x80015A50u, func_80015A50, 0x00000000u, 0x0u},
    {0x80015A94u, func_80015A94, 0x00000000u, 0x0u},
    {0x80015AD8u, Fade_WaitInitOut, 0x00000000u, 0x0u},
    {0x80015B00u, Fade_WaitOut, 0x00000000u, 0x0u},
    {0x80015B28u, Fade_WaitInitOutColor, 0x00000000u, 0x0u},
    {0x80015B50u, func_80015B50, 0x00000000u, 0x0u},
    {0x80015B94u, func_80015B94, 0x00000000u, 0x0u},
    {0x80015BD8u, Fade_SetTargetLevel, 0x00000000u, 0x0u},
    {0x80015BF0u, Fade_SetLevel, 0x00000000u, 0x0u},
    {0x80015C0Cu, Fade_StartInKeepOverlay, 0x00000000u, 0x0u},
    {0x80015C48u, Fade_StartInKeepOverlayAndHideSecondaryTables, 0x00000000u, 0x0u},
    {0x80015C84u, Fade_StartOutKeepOverlay, 0x00000000u, 0x0u},
    {0x80015CC0u, Fade_StartOutKeepOverlayAndHideSecondaryTables, 0x00000000u, 0x0u},
    {0x80015CFCu, Fade_EnableOrderingTables, 0x00000000u, 0x0u},
    {0x80015D0Cu, Fade_DisableOrderingTables, 0x00000000u, 0x0u},
    {0x80015D18u, func_80015D18, 0x00000000u, 0x0u},
    {0x80015DB8u, func_80015DB8, 0x00000000u, 0x0u},
    {0x80015DFCu, func_80015DFC, 0x00000000u, 0x0u},
    {0x80015EF4u, func_80015EF4, 0x00000000u, 0x0u},
    {0x800164FCu, Duel_DrawFieldCards, 0x00000000u, 0x0u},
    {0x80016778u, DisplayObject_SetResourceVariantFromSign, 0x00000000u, 0x0u},
    {0x80016784u, func_80016784, 0x00000000u, 0x0u},
    {0x80016D04u, Duel_DrawCardAtOutputPosition, 0x00000000u, 0x0u},
    {0x80016D2Cu, func_80016D2C, 0x00000000u, 0x0u},
    {0x80016DDCu, Duel_UpdateLifePointDisplay, 0x00000000u, 0x0u},
    {0x80016E70u, Duel_DrawLifePointsAndDeckCounts, 0x00000000u, 0x0u},
    {0x8001700Cu, DuelCard_CanActThisTurn, 0x00000000u, 0x0u},
    {0x80017034u, Duel_GetCardViewerRequestId, 0x00000000u, 0x0u},
    {0x800170C8u, Duel_CalcCardStats, 0x00000000u, 0x0u},
    {0x80017130u, func_80017130, 0x00000000u, 0x0u},
    {0x800171A8u, Duel_LoadPackageStage, 0x00000000u, 0x0u},
    {0x8001755Cu, Duel_InitModelScene, 0x00000000u, 0x0u},
    {0x800175A0u, Duel_InitSideStates, 0x00000000u, 0x0u},
    {0x800176D0u, Duel_ClearHandSlots, 0x00000000u, 0x0u},
    {0x80017708u, Duel_InitSelectionRecords, 0x00000000u, 0x0u},
    {0x8001778Cu, Duel_ResetCardRecords, 0x00000000u, 0x0u},
    {0x800177C4u, func_800177C4, 0x00000000u, 0x0u},
    {0x800178BCu, func_800178BC, 0x00000000u, 0x0u},
    {0x8001798Cu, Duel_LoadTerrainPackage, 0x00000000u, 0x0u},
    {0x800179F4u, Duel_InitScene, 0x00000000u, 0x0u},
    {0x80017DB4u, func_80017DB4, 0x00000000u, 0x0u},
    {0x80017E3Cu, func_80017E3C, 0x00000000u, 0x0u},
    {0x80017F04u, func_80017F04, 0x00000000u, 0x0u},
    {0x80018004u, func_80018004, 0x00000000u, 0x0u},
    {0x80018080u, Duel_ApplyCardObjectFlags, 0x00000000u, 0x0u},
    {0x80018150u, func_80018150, 0x00000000u, 0x0u},
    {0x800181ECu, Duel_GetCardEffectVariant, 0x00000000u, 0x0u},
    {0x8001825Cu, DuelScene_UpdateResume, 0x00000000u, 0x0u},
    {0x80018608u, DuelScene_UpdateStartup, 0x00000000u, 0x0u},
    {0x8001898Cu, DuelScene_UpdateDrawPhase, 0x00000000u, 0x0u},
    {0x80018C34u, Duel_UpdateDrawCardSlide, 0x00000000u, 0x0u},
    {0x80018CF8u, Duel_HasAllExodiaPieces, 0x00000000u, 0x0u},
    {0x80018DB4u, DuelScene_UpdateDrawResolution, 0x00000000u, 0x0u},
    {0x80018FECu, DuelScene_UpdateExodiaResult, 0x00000000u, 0x0u},
    {0x8001944Cu, DuelCard_CaptureRoundedTexture, 0x00000000u, 0x0u},
    {0x80019564u, Duel_CreateCardEffectOverlay, 0x00000000u, 0x0u},
    {0x80019608u, DuelScene_UpdateCardUse, 0x00000000u, 0x0u},
    {0x80019A08u, Duel_CheckEquip, 0x00000000u, 0x0u},
    {0x80019A60u, Duel_CheckFusion, 0x00000000u, 0x0u},
    {0x80019B2Cu, DisplayObject_UpdateAlphaTransition, 0x00000000u, 0x0u},
    {0x80019BA0u, func_80019BA0, 0x00000000u, 0x0u},
    {0x80019BD0u, func_80019BD0, 0x00000000u, 0x0u},
    {0x80019CC8u, func_80019CC8, 0x00000000u, 0x0u},
    {0x80019D18u, DuelScene_UpdateCardPlacement, 0x00000000u, 0x0u},
    {0x8001B0CCu, func_8001B0CC, 0x00000000u, 0x0u},
    {0x8001B170u, func_8001B170, 0x00000000u, 0x0u},
    {0x8001B780u, func_8001B780, 0x00000000u, 0x0u},
    {0x8001B7ACu, func_8001B7AC, 0x00000000u, 0x0u},
    {0x8001B8B8u, func_8001B8B8, 0x00000000u, 0x0u},
    {0x8001B938u, func_8001B938, 0x00000000u, 0x0u},
    {0x8001BAF0u, func_8001BAF0, 0x00000000u, 0x0u},
    {0x8001BD48u, Duel_CheckQuitInput, 0x00000000u, 0x0u},
    {0x8001BD88u, DuelScene_UpdateHandActions, 0x00000000u, 0x0u},
    {0x8001D240u, DuelCard_UpdateDefenseRotation, 0x00000000u, 0x0u},
    {0x8001D344u, func_8001D344, 0x00000000u, 0x0u},
    {0x8001D3C4u, func_8001D3C4, 0x00000000u, 0x0u},
    {0x8001D518u, func_8001D518, 0x00000000u, 0x0u},
    {0x8001D5B4u, func_8001D5B4, 0x00000000u, 0x0u},
    {0x8001D670u, DuelScene_UpdateFieldActions, 0x00000000u, 0x0u},
    {0x8001EC70u, func_8001EC70, 0x00000000u, 0x0u},
    {0x8001ED20u, func_8001ED20, 0x00000000u, 0x0u},
    {0x8001EE44u, Duel_CalcGuardianStarBonus, 0x00000000u, 0x0u},
    {0x8001EF1Cu, Duel_CalcBattleAttack, 0x00000000u, 0x0u},
    {0x8001EF78u, Duel_CalcBattleDefense, 0x00000000u, 0x0u},
    {0x8001EFD4u, func_8001EFD4, 0x00000000u, 0x0u},
    {0x8001F0D0u, Duel_SelectAttackTrap, 0x00000000u, 0x0u},
    {0x8001F364u, Duel_UpdateTrapPresentation, 0x00000000u, 0x0u},
    {0x8001F55Cu, DuelScene_UpdateBattle, 0x00000000u, 0x0u},
    {0x800208D4u, DuelScene_UpdateTurnSwitch, 0x00000000u, 0x0u},
    {0x80020988u, func_80020988, 0x00000000u, 0x0u},
    {0x80020BE4u, func_80020BE4, 0x00000000u, 0x0u},
    {0x80020D4Cu, DuelResult_UpdateOrbitSprite, 0x00000000u, 0x0u},
    {0x80020EE8u, func_80020EE8, 0x00000000u, 0x0u},
    {0x80020F4Cu, DuelScene_UpdateResultOutro, 0x00000000u, 0x0u},
    {0x80021480u, Duel_ShowResultPage, 0x00000000u, 0x0u},
    {0x80021558u, Duel_CalcRankScoreChange, 0x00000000u, 0x0u},
    {0x80021598u, Duel_CalcRankScore, 0x00000000u, 0x0u},
    {0x80021810u, Duel_SelectCardDrop, 0x00000000u, 0x0u},
    {0x80021894u, Duel_AwardCard, 0x00000000u, 0x0u},
    {0x800218F0u, DuelScene_UpdateResultRewards, 0x00000000u, 0x0u},
    {0x800220B8u, func_800220B8, 0x00000000u, 0x0u},
    {0x800222F4u, func_800222F4, 0x00000000u, 0x0u},
    {0x80022618u, DuelScene_UpdateEffectPreview, 0x00000000u, 0x0u},
    {0x80022674u, func_80022674, 0x00000000u, 0x0u},
    {0x800229F4u, func_800229F4, 0x00000000u, 0x0u},
    {0x80022D94u, func_80022D94, 0x00000000u, 0x0u},
    {0x80022EECu, DuelSelection_UpdateLinkedObject, 0x00000000u, 0x0u},
    {0x80022F98u, DuelSelection_LinkDisplayObject, 0x00000000u, 0x0u},
    {0x80022FF0u, DuelSelection_LinkDisplayObjects, 0x00000000u, 0x0u},
    {0x80023090u, func_80023090, 0x00000000u, 0x0u},
    {0x80023144u, func_80023144, 0x00000000u, 0x0u},
    {0x8002348Cu, func_8002348C, 0x00000000u, 0x0u},
    {0x800234E4u, func_800234E4, 0x00000000u, 0x0u},
    {0x800235C0u, func_800235C0, 0x00000000u, 0x0u},
    {0x80023D08u, func_80023D08, 0x00000000u, 0x0u},
    {0x80023FBCu, func_80023FBC, 0x00000000u, 0x0u},
    {0x80024060u, func_80024060, 0x00000000u, 0x0u},
    {0x80024088u, func_80024088, 0x00000000u, 0x0u},
    {0x800240B0u, Duel_UpdateCardPickCursor, 0x00000000u, 0x0u},
    {0x80024200u, DuelScene_Update, 0x00000000u, 0x0u},
    {0x80024388u, DuelScene_UpdateWithSideInput, 0x00000000u, 0x0u},
    {0x800243F4u, Duel_ShuffleDeck, 0x00000000u, 0x0u},
    {0x800245A0u, Duel_ShuffleBothDecks, 0x00000000u, 0x0u},
    {0x800245ECu, Duel_StepCardDataTransfer, 0x00000000u, 0x0u},
    {0x80024704u, Util_CompareS16, 0x00000000u, 0x0u},
    {0x80024734u, Duel_RequestCombinedDeckData, 0x00000000u, 0x0u},
    {0x80024824u, Duel_PopulateCombinedDeckData, 0x00000000u, 0x0u},
    {0x80024914u, DuelCard_DeactivateRecord, 0x00000000u, 0x0u},
    {0x80024954u, DuelCard_RemoveFromField, 0x00000000u, 0x0u},
    {0x8002497Cu, Duel_GetTerrainBoost, 0x00000000u, 0x0u},
    {0x800249E0u, Duel_SetupCardRecord, 0x00000000u, 0x0u},
    {0x80024C1Cu, func_80024C1C, 0x00000000u, 0x0u},
    {0x80024D34u, func_80024D34, 0x00000000u, 0x0u},
    {0x80024DC8u, func_80024DC8, 0x00000000u, 0x0u},
    {0x80024E24u, DuelEffect_MarkInitialized, 0x00000000u, 0x0u},
    {0x80024E4Cu, DuelEffect_ClearCardEffect, 0x00000000u, 0x0u},
    {0x80024E58u, DuelEffect_ApplyTerrain, 0x00000000u, 0x0u},
    {0x80025028u, Duel_SelectTrapByCardId, 0x00000000u, 0x0u},
    {0x800250C8u, DuelEffect_ApplyLifePointRecovery, 0x00000000u, 0x0u},
    {0x8002525Cu, DuelEffect_ApplyDirectDamage, 0x00000000u, 0x0u},
    {0x8002538Cu, DuelEffect_ApplyMonsterRemoval, 0x00000000u, 0x0u},
    {0x800255FCu, DuelEffect_ApplyStopDefense, 0x00000000u, 0x0u},
    {0x800257A0u, DuelEffect_ApplyBoardDestruction, 0x00000000u, 0x0u},
    {0x8002596Cu, DuelEffect_ApplyRaigeki, 0x00000000u, 0x0u},
    {0x80025B28u, DuelEffect_UpdateRevealCard, 0x00000000u, 0x0u},
    {0x80025BECu, DuelEffect_ApplyDarkPiercingLight, 0x00000000u, 0x0u},
    {0x80025D30u, DuelEffect_ApplyStatPenalty, 0x00000000u, 0x0u},
    {0x80025EE0u, DuelEffect_StartSwords, 0x00000000u, 0x0u},
    {0x80025F3Cu, DuelEffect_ApplySwords, 0x00000000u, 0x0u},
    {0x800260D0u, DuelEffect_ApplyCursebreaker, 0x00000000u, 0x0u},
    {0x8002622Cu, DuelEffect_StartRitual, 0x00000000u, 0x0u},
    {0x800262D4u, DuelEffect_ApplyRitual, 0x00000000u, 0x0u},
    {0x80026A3Cu, DuelEffect_ApplyHarpiesFeatherDuster, 0x00000000u, 0x0u},
    {0x80026B34u, DuelEffect_UpdateCardEffect, 0x00000000u, 0x0u},
    {0x80026BA4u, DuelEffect_StartCardEffect, 0x00000000u, 0x0u},
    {0x80026C0Cu, Duel_FindFreeFieldSlot, 0x00000000u, 0x0u},
    {0x80026C6Cu, Duel_CollectFieldCardsBelowType, 0x00000000u, 0x0u},
    {0x80026D18u, Duel_CollectFieldCardsByType, 0x00000000u, 0x0u},
    {0x80026DC8u, Duel_SelectEquipPair, 0x00000000u, 0x0u},
    {0x80027060u, Duel_SelectTrapPlay, 0x00000000u, 0x0u},
    {0x8002712Cu, func_8002712C, 0x00000000u, 0x0u},
    {0x80027228u, func_80027228, 0x00000000u, 0x0u},
    {0x80027508u, func_80027508, 0x00000000u, 0x0u},
    {0x8002778Cu, func_8002778C, 0x00000000u, 0x0u},
    {0x800278A0u, func_800278A0, 0x00000000u, 0x0u},
    {0x800279BCu, func_800279BC, 0x00000000u, 0x0u},
    {0x80027DF8u, func_80027DF8, 0x00000000u, 0x0u},
    {0x80028220u, func_80028220, 0x00000000u, 0x0u},
    {0x80028260u, DuelCard_DecodeTaggedSlotIndex, 0x00000000u, 0x0u},
    {0x8002827Cu, func_8002827C, 0x00000000u, 0x0u},
    {0x800282E8u, DuelEffect_MarkStateInitialized, 0x00000000u, 0x0u},
    {0x80028310u, DuelEffect_UpdateDialogState, 0x00000000u, 0x0u},
    {0x800283ECu, func_800283EC, 0x00000000u, 0x0u},
    {0x800283F4u, DuelEffect_UpdateCardViewerState, 0x00000000u, 0x0u},
    {0x8002892Cu, DuelEffect_UpdateState, 0x00000000u, 0x0u},
    {0x800289ACu, func_800289AC, 0x00000000u, 0x0u},
    {0x800289B4u, func_800289B4, 0x00000000u, 0x0u},
    {0x800289BCu, func_800289BC, 0x00000000u, 0x0u},
    {0x80028B08u, func_80028B08, 0x00000000u, 0x0u},
    {0x80029108u, CardPreview_UpdateVariant, 0x00000000u, 0x0u},
    {0x80029164u, func_80029164, 0x00000000u, 0x0u},
    {0x800291E0u, func_800291E0, 0x00000000u, 0x0u},
    {0x80029528u, func_80029528, 0x00000000u, 0x0u},
    {0x80029574u, DuelEffect_ClearResourceObjectPointers, 0x00000000u, 0x0u},
    {0x80029590u, func_80029590, 0x00000000u, 0x0u},
    {0x80029684u, func_80029684, 0x00000000u, 0x0u},
    {0x800297DCu, func_800297DC, 0x00000000u, 0x0u},
    {0x80029934u, func_80029934, 0x00000000u, 0x0u},
    {0x80029EB0u, Library_GetCardFlags, 0x00000000u, 0x0u},
    {0x80029EC4u, Library_DrawCardGrid, 0x00000000u, 0x0u},
    {0x8002A2F4u, func_8002A2F4, 0x00000000u, 0x0u},
    {0x8002A3CCu, func_8002A3CC, 0x00000000u, 0x0u},
    {0x8002A4A8u, func_8002A4A8, 0x00000000u, 0x0u},
    {0x8002A660u, func_8002A660, 0x00000000u, 0x0u},
    {0x8002A6B8u, Library_GetGridCursorCardId, 0x00000000u, 0x0u},
    {0x8002A788u, Library_UpdateGridCursor, 0x00000000u, 0x0u},
    {0x8002A9C0u, func_8002A9C0, 0x00000000u, 0x0u},
    {0x8002ABB4u, func_8002ABB4, 0x00000000u, 0x0u},
    {0x8002ACA4u, func_8002ACA4, 0x00000000u, 0x0u},
    {0x8002BAA0u, func_8002BAA0, 0x00000000u, 0x0u},
    {0x8002BAACu, func_8002BAAC, 0x00000000u, 0x0u},
    {0x8002BAB4u, func_8002BAB4, 0x00000000u, 0x0u},
    {0x8002BD0Cu, func_8002BD0C, 0x00000000u, 0x0u},
    {0x8002BF3Cu, Library_MarkOwnedCards, 0x00000000u, 0x0u},
    {0x8002BFCCu, func_8002BFCC, 0x00000000u, 0x0u},
    {0x8002C400u, func_8002C400, 0x00000000u, 0x0u},
    {0x8002C484u, func_8002C484, 0x00000000u, 0x0u},
    {0x8002C4DCu, Duel_FindPlayerDeckCard, 0x00000000u, 0x0u},
    {0x8002C518u, Library_CheckCardOwned, 0x00000000u, 0x0u},
    {0x8002C560u, func_8002C560, 0x00000000u, 0x0u},
    {0x8002C568u, func_8002C568, 0x00000000u, 0x0u},
    {0x8002C570u, func_8002C570, 0x00000000u, 0x0u},
    {0x8002C598u, DuelEffect_ResetRequestPool, 0x00000000u, 0x0u},
    {0x8002C5CCu, DuelEffect_FindFreeRequest, 0x00000000u, 0x0u},
    {0x8002C604u, DuelEffect_AllocateRequest, 0x00000000u, 0x0u},
    {0x8002C68Cu, DuelEffect_CreateRequest, 0x00000000u, 0x0u},
    {0x8002C6C8u, DuelEffect_UpdateRequests, 0x00000000u, 0x0u},
    {0x8002C7E8u, Duel_CheckRitual, 0x00000000u, 0x0u},
    {0x8002C938u, Duel_CollectFieldRowCardObjects, 0x00000000u, 0x0u},
    {0x8002C9B4u, Duel_CollectMatchingFieldCardObjects, 0x00000000u, 0x0u},
    {0x8002CB50u, DisplayObject_CopyWorkSlots, 0x00000000u, 0x0u},
    {0x8002CB80u, Duel_CalcGuardianStarMatchup, 0x00000000u, 0x0u},
    {0x8002CBF4u, Duel_GetBaseCardStat, 0x00000000u, 0x0u},
    {0x8002CCA8u, Campaign_TestStoryFlag, 0x00000000u, 0x0u},
    {0x8002CCE4u, Library_UpdateCardUsedFlag, 0x00000000u, 0x0u},
    {0x8002CD48u, Campaign_EnsureStoryFlag, 0x00000000u, 0x0u},
    {0x8002CD8Cu, Main_ResetFrontendRuntime, 0x00000000u, 0x0u},
    {0x8002CDE8u, Main_PrepareFrontendLoop, 0x00000000u, 0x0u},
    {0x8002CE08u, Main_RunDebugMenu, 0x00000000u, 0x0u},
    {0x8002CE64u, Main_RunCampaign, 0x00000000u, 0x0u},
    {0x8002CEE8u, Main_RunDuel, 0x00000000u, 0x0u},
    {0x8002D0E0u, Main_RunLibraryMenu, 0x00000000u, 0x0u},
    {0x8002D180u, Main_RunAnimatedBattle, 0x00000000u, 0x0u},
    {0x8002D2D8u, Main_RunCampaignMap, 0x00000000u, 0x0u},
    {0x8002D370u, Main_RunBuildDeckMenu, 0x00000000u, 0x0u},
    {0x8002D3F8u, Main_RunFreeDuelMenu, 0x00000000u, 0x0u},
    {0x8002D458u, Main_ApplyMenuSelection, 0x00000000u, 0x0u},
    {0x8002D588u, Main_RunMenu, 0x00000000u, 0x0u},
    {0x8002D62Cu, Main_RunNameEntry, 0x00000000u, 0x0u},
    {0x8002D684u, Main_RunPasswordMenu, 0x00000000u, 0x0u},
    {0x8002D6C8u, Main_RunOptionsMenu, 0x00000000u, 0x0u},
    {0x8002D730u, Main_RunGameOver, 0x00000000u, 0x0u},
    {0x8002D7C4u, Main_RunUnusedDeveloperMode, 0x00000000u, 0x0u},
    {0x8002D7CCu, Main_RunTrade, 0x00000000u, 0x0u},
    {0x8002DA1Cu, Main_RunCredits, 0x00000000u, 0x0u},
    {0x8002DC38u, Main_RunTwoPlayerDuelSetup, 0x00000000u, 0x0u},
    {0x8002DD74u, Main_Loop, 0x00000000u, 0x0u},
    {0x8002DDFCu, ScriptImage_TransferCallback, 0x00000000u, 0x0u},
    {0x8002DF2Cu, ScriptImage_RequestTransfer, 0x00000000u, 0x0u},
    {0x8002E00Cu, ScriptImage_ReleaseObjects, 0x00000000u, 0x0u},
    {0x8002E060u, ScriptImage_CreateObject, 0x00000000u, 0x0u},
    {0x8002E128u, ScriptImage_RebuildObjects, 0x00000000u, 0x0u},
    {0x8002E370u, DuelEffect_MarkObjectIfActive, 0x00000000u, 0x0u},
    {0x8002E3B4u, ScriptCommand_MarkStarted, 0x00000000u, 0x0u},
    {0x8002E3DCu, Script_OpHalt, 0x00000000u, 0x0u},
    {0x8002E3FCu, Campaign_CreatePrimaryDisplayObject, 0x00000000u, 0x0u},
    {0x8002E470u, Script_OpLoadImageScene, 0x00000000u, 0x0u},
    {0x8002E5ACu, Script_OpShowDialog, 0x00000000u, 0x0u},
    {0x8002E6B8u, Script_OpStageImage, 0x00000000u, 0x0u},
    {0x8002E730u, Script_OpShowImage, 0x00000000u, 0x0u},
    {0x8002E918u, Script_OpStoryFlag, 0x00000000u, 0x0u},
    {0x8002E9A0u, Script_OpViewportTween, 0x00000000u, 0x0u},
    {0x8002EA0Cu, Script_UpdateViewportTween, 0x00000000u, 0x0u},
    {0x8002EB48u, Script_OpOpenCampaignMap, 0x00000000u, 0x0u},
    {0x8002EB78u, Script_OpShowMenu, 0x00000000u, 0x0u},
    {0x8002EC74u, Script_OpSound, 0x00000000u, 0x0u},
    {0x8002EDB0u, Script_OpFadeBgm, 0x00000000u, 0x0u},
    {0x8002EE20u, Script_OpJump, 0x00000000u, 0x0u},
    {0x8002EE5Cu, Duel_IsPlayerDeckComplete, 0x00000000u, 0x0u},
    {0x8002EE94u, Script_OpSavePrompt, 0x00000000u, 0x0u},
    {0x8002F430u, Script_OpUnusedHalt14, 0x00000000u, 0x0u},
    {0x8002F438u, Script_OpUnusedHalt15, 0x00000000u, 0x0u},
    {0x8002F440u, Script_OpFadeOut, 0x00000000u, 0x0u},
    {0x8002F4C0u, func_8002F4C0, 0x00000000u, 0x0u},
    {0x8002F630u, Script_OpDuelResult, 0x00000000u, 0x0u},
    {0x8002F930u, Script_OpGameOver, 0x00000000u, 0x0u},
    {0x8002F94Cu, Script_OpCredits, 0x00000000u, 0x0u},
    {0x8002F968u, Script_OpWait, 0x00000000u, 0x0u},
    {0x8002F9D4u, Script_OpJumpIfDeckIncomplete, 0x00000000u, 0x0u},
    {0x8002FA28u, Script_OpReturnToMenu, 0x00000000u, 0x0u},
    {0x8002FA54u, Script_RunTick, 0x00000000u, 0x0u},
    {0x8002FB78u, Campaign_LoadScenePackageStage, 0x00000000u, 0x0u},
    {0x8002FD10u, Campaign_LoadScenePackage, 0x00000000u, 0x0u},
    {0x8002FED0u, SceneScript_NoOpRecordCallback, 0x00000000u, 0x0u},
    {0x8002FED8u, func_8002FED8, 0x00000000u, 0x0u},
    {0x8002FFD4u, SceneScript_UpdateSlots, 0x00000000u, 0x0u},
    {0x80030050u, Script_ReadByte, 0x00000000u, 0x0u},
    {0x8003006Cu, Script_ReadU16LE, 0x00000000u, 0x0u},
    {0x80030090u, DebugMenu_DimPrimaryDisplayObject, 0x00000000u, 0x0u},
    {0x800300ACu, DebugMenu_RestorePrimaryDisplayObject, 0x00000000u, 0x0u},
    {0x800300C8u, DebugMenu_UpdateCursorLayout, 0x00000000u, 0x0u},
    {0x80030198u, DebugMenu_Init, 0x00000000u, 0x0u},
    {0x80030250u, func_80030250, 0x00000000u, 0x0u},
    {0x80030294u, func_80030294, 0x00000000u, 0x0u},
    {0x800307B8u, DebugMenu_UpdateSoundEntry, 0x00000000u, 0x0u},
    {0x80030998u, DebugMenu_UpdateCampaignEntry, 0x00000000u, 0x0u},
    {0x80030C10u, func_80030C10, 0x00000000u, 0x0u},
    {0x80030CB0u, DebugMenu_UpdateTitleEntry, 0x00000000u, 0x0u},
    {0x80030D5Cu, DebugMenu_UpdateMovieEntry, 0x00000000u, 0x0u},
    {0x80030E30u, DebugMenu_UpdateLoadEntry, 0x00000000u, 0x0u},
    {0x80030E7Cu, DebugMenu_UpdateSaveEntry, 0x00000000u, 0x0u},
    {0x80030EC8u, DebugMenu_UpdateTradeEntry, 0x00000000u, 0x0u},
    {0x80030F40u, DebugMenu_EnterDuel, 0x00000000u, 0x0u},
    {0x80030F80u, DebugMenu_EnterDeckEditor, 0x00000000u, 0x0u},
    {0x80030FA0u, DebugMenu_EnterMappedMode, 0x00000000u, 0x0u},
    {0x80030FD0u, DebugMenu_Exit, 0x00000000u, 0x0u},
    {0x80031000u, DebugMenu_UpdateTwoPlayerDuelEntry, 0x00000000u, 0x0u},
    {0x80031078u, DebugMenu_ResetEntryState, 0x00000000u, 0x0u},
    {0x80031084u, DebugMenu_Update, 0x00000000u, 0x0u},
    {0x8003134Cu, func_8003134C, 0x00000000u, 0x0u},
    {0x80031354u, DebugMenu_UpdateBustUpEntry, 0x00000000u, 0x0u},
    {0x800313E8u, func_800313E8, 0x00000000u, 0x0u},
    {0x80031574u, func_80031574, 0x00000000u, 0x0u},
    {0x800316F0u, func_800316F0, 0x00000000u, 0x0u},
    {0x80031784u, BuildDeck_DrawSortIcons, 0x00000000u, 0x0u},
    {0x80031874u, func_80031874, 0x00000000u, 0x0u},
    {0x80031CD4u, CardList_CreateSlotTextBox, 0x00000000u, 0x0u},
    {0x80031E04u, func_80031E04, 0x00000000u, 0x0u},
    {0x80031E5Cu, BuildDeck_RefreshCountDisplay, 0x00000000u, 0x0u},
    {0x80031EE4u, BuildDeck_ReturnCardToChest, 0x00000000u, 0x0u},
    {0x80031F7Cu, BuildDeck_TakeCardFromChest, 0x00000000u, 0x0u},
    {0x8003201Cu, func_8003201C, 0x00000000u, 0x0u},
    {0x800320BCu, BuildDeck_AddCard, 0x00000000u, 0x0u},
    {0x80032184u, func_80032184, 0x00000000u, 0x0u},
    {0x80032328u, func_80032328, 0x00000000u, 0x0u},
    {0x80032370u, func_80032370, 0x00000000u, 0x0u},
    {0x800323F8u, func_800323F8, 0x00000000u, 0x0u},
    {0x80032B38u, BuildDeck_TestAndSetInitialized, 0x00000000u, 0x0u},
    {0x80032B60u, BuildDeck_CompareCard, 0x00000000u, 0x0u},
    {0x80032BD4u, func_80032BD4, 0x00000000u, 0x0u},
    {0x80032C48u, func_80032C48, 0x00000000u, 0x0u},
    {0x800330BCu, BuildDeck_UpdateCardListInput, 0x00000000u, 0x0u},
    {0x80033500u, BuildDeck_GetActiveCardID, 0x00000000u, 0x0u},
    {0x8003353Cu, BuildDeck_UpdateDeckPaneInput, 0x00000000u, 0x0u},
    {0x800336F0u, BuildDeck_UpdateChestPaneInput, 0x00000000u, 0x0u},
    {0x800338E4u, BuildDeck_UpdatePaneTransition, 0x00000000u, 0x0u},
    {0x80033998u, BuildDeck_HasOpenDeckSlot, 0x00000000u, 0x0u},
    {0x800339D0u, func_800339D0, 0x00000000u, 0x0u},
    {0x80033BE8u, func_80033BE8, 0x00000000u, 0x0u},
    {0x80033C90u, BuildDeck_EnterNarrowConfirmMode, 0x00000000u, 0x0u},
    {0x80033CA8u, BuildDeck_EnterWideConfirmMode, 0x00000000u, 0x0u},
    {0x80033CC4u, CardList_UpdateSortMode, 0x00000000u, 0x0u},
    {0x80033CF8u, func_80033CF8, 0x00000000u, 0x0u},
    {0x80033DB0u, func_80033DB0, 0x00000000u, 0x0u},
    {0x80034830u, func_80034830, 0x00000000u, 0x0u},
    {0x80035598u, SortedEntry_Compare, 0x00000000u, 0x0u},
    {0x800355C8u, SortedEntry_SortAndRelink, 0x00000000u, 0x0u},
    {0x80035668u, func_80035668, 0x00000000u, 0x0u},
    {0x80035680u, SortedEntry_BeginCollection, 0x00000000u, 0x0u},
    {0x800356A0u, Util_CopyWords, 0x00000000u, 0x0u},
    {0x80035748u, Util_FillMemory, 0x00000000u, 0x0u},
    {0x800357E8u, Text_EncodeDecimalDigits, 0x00000000u, 0x0u},
    {0x800358A0u, Text_EncodeDecimalNoPadding, 0x00000000u, 0x0u},
    {0x800358FCu, Rand_GetInterval, 0x00000000u, 0x0u},
    {0x8003594Cu, Movie_Play, 0x00000000u, 0x0u},
    {0x800359B0u, func_800359B0, 0x00000000u, 0x0u},
    {0x80035A58u, Movie_ResetPlaybackState, 0x00000000u, 0x0u},
    {0x80035A64u, func_80035A64, 0x00000000u, 0x0u},
    {0x80035AB8u, TextBox_SetRect, 0x00000000u, 0x0u},
    {0x80035AF0u, DuelEffect_InitEntry, 0x00000000u, 0x0u},
    {0x80035B7Cu, TextBox_Destroy, 0x00000000u, 0x0u},
    {0x80035BE4u, TextBox_Create, 0x00000000u, 0x0u},
    {0x80035C38u, TextBox_CreateFlagged, 0x00000000u, 0x0u},
    {0x80035CA8u, func_80035CA8, 0x00000000u, 0x0u},
    {0x80035CE4u, DuelEffect_ResetOccupancy, 0x00000000u, 0x0u},
    {0x80035D10u, func_80035D10, 0x00000000u, 0x0u},
    {0x80035DB8u, DuelEffect_ClearMatchingMarker, 0x00000000u, 0x0u},
    {0x80035DF4u, DuelEffect_ResetEntryMarkers, 0x00000000u, 0x0u},
    {0x80035E20u, func_80035E20, 0x00000000u, 0x0u},
    {0x80036BCCu, Text_FindRecordById, 0x00000000u, 0x0u},
    {0x80036C14u, DuelEffect_AppendEntry, 0x00000000u, 0x0u},
    {0x80036D3Cu, TextStream_ReadU16LE, 0x00000000u, 0x0u},
    {0x80036D70u, TextStream_ReadU32LE, 0x00000000u, 0x0u},
    {0x80036DBCu, DuelEffect_UpdateObjectLayout, 0x00000000u, 0x0u},
    {0x80036F80u, Dialog_HighlightChoice, 0x00000000u, 0x0u},
    {0x8003700Cu, Dialog_ReadChoiceInput, 0x00000000u, 0x0u},
    {0x80037110u, Widget_UpdatePulseColour, 0x00000000u, 0x0u},
    {0x800371A8u, Dialog_UpdateChoice, 0x00000000u, 0x0u},
    {0x8003735Cu, DuelEffect_HasActiveEntry, 0x00000000u, 0x0u},
    {0x800373C8u, func_800373C8, 0x00000000u, 0x0u},
    {0x8003741Cu, Text_CompletePageAdvance, 0x00000000u, 0x0u},
    {0x800374A8u, func_800374A8, 0x00000000u, 0x0u},
    {0x800374F4u, Dialog_OpenChoice, 0x00000000u, 0x0u},
    {0x800375A4u, func_800375A4, 0x00000000u, 0x0u},
    {0x8003767Cu, func_8003767C, 0x00000000u, 0x0u},
    {0x8003771Cu, func_8003771C, 0x00000000u, 0x0u},
    {0x800377ACu, TextBox_WaitForScriptCompletion, 0x00000000u, 0x0u},
    {0x800377C8u, func_800377C8, 0x00000000u, 0x0u},
    {0x8003787Cu, func_8003787C, 0x00000000u, 0x0u},
    {0x800378D8u, func_800378D8, 0x00000000u, 0x0u},
    {0x80037914u, func_80037914, 0x00000000u, 0x0u},
    {0x80037950u, func_80037950, 0x00000000u, 0x0u},
    {0x8003798Cu, func_8003798C, 0x00000000u, 0x0u},
    {0x800379C4u, func_800379C4, 0x00000000u, 0x0u},
    {0x800379F8u, func_800379F8, 0x00000000u, 0x0u},
    {0x80037A58u, func_80037A58, 0x00000000u, 0x0u},
    {0x80037B40u, func_80037B40, 0x00000000u, 0x0u},
    {0x80037C74u, TextBox_WrapLineIfNeeded, 0x00000000u, 0x0u},
    {0x80037CE0u, Text_TryCompleteChoiceLayout, 0x00000000u, 0x0u},
    {0x80037D2Cu, Text_ExtendGlyphCode, 0x00000000u, 0x0u},
    {0x80037D6Cu, Text_SetStateFromStream, 0x00000000u, 0x0u},
    {0x80037DA4u, func_80037DA4, 0x00000000u, 0x0u},
    {0x80038024u, func_80038024, 0x00000000u, 0x0u},
    {0x80038070u, func_80038070, 0x00000000u, 0x0u},
    {0x80038094u, func_80038094, 0x00000000u, 0x0u},
    {0x800380D4u, func_800380D4, 0x00000000u, 0x0u},
    {0x80038110u, func_80038110, 0x00000000u, 0x0u},
    {0x80038148u, func_80038148, 0x00000000u, 0x0u},
    {0x800382A8u, func_800382A8, 0x00000000u, 0x0u},
    {0x80038334u, func_80038334, 0x00000000u, 0x0u},
    {0x80038388u, func_80038388, 0x00000000u, 0x0u},
    {0x800383B0u, func_800383B0, 0x00000000u, 0x0u},
    {0x800383DCu, func_800383DC, 0x00000000u, 0x0u},
    {0x80038498u, func_80038498, 0x00000000u, 0x0u},
    {0x800384E4u, func_800384E4, 0x00000000u, 0x0u},
    {0x80038530u, Text_StartCampaignDuel, 0x00000000u, 0x0u},
    {0x80038690u, DuelEffect_PlayBgmCommand, 0x00000000u, 0x0u},
    {0x800386B8u, DuelEffect_ProcessBgmCommand, 0x00000000u, 0x0u},
    {0x80038798u, DuelEffect_PlaySoundCommand, 0x00000000u, 0x0u},
    {0x80038800u, DuelEffect_FadeOutBgmCommand, 0x00000000u, 0x0u},
    {0x80038888u, func_80038888, 0x00000000u, 0x0u},
    {0x80038890u, func_80038890, 0x00000000u, 0x0u},
    {0x80038898u, func_80038898, 0x00000000u, 0x0u},
    {0x800388D8u, Text_ApplyFadeCommand, 0x00000000u, 0x0u},
    {0x800389C4u, func_800389C4, 0x00000000u, 0x0u},
    {0x800389D8u, func_800389D8, 0x00000000u, 0x0u},
    {0x80038A44u, func_80038A44, 0x00000000u, 0x0u},
    {0x80038AB0u, Text_UnlockDuelist, 0x00000000u, 0x0u},
    {0x80038B08u, Text_CloseChoice, 0x00000000u, 0x0u},
    {0x80038B4Cu, Text_DispatchSecondaryCommand, 0x00000000u, 0x0u},
    {0x80038BA8u, Text_SetCursorOffset, 0x00000000u, 0x0u},
    {0x80038BF0u, Text_HandleChoiceCommand, 0x00000000u, 0x0u},
    {0x80038D14u, Text_StartPageWait, 0x00000000u, 0x0u},
    {0x80038D2Cu, Text_HandleCampaignFlagCommand, 0x00000000u, 0x0u},
    {0x80038DB8u, Text_PushStreamOffset, 0x00000000u, 0x0u},
    {0x80038E1Cu, Text_NewLine, 0x00000000u, 0x0u},
    {0x80038E7Cu, Text_EndStream, 0x00000000u, 0x0u},
    {0x80038EB0u, Text_HandleDisplayEffectCommand, 0x00000000u, 0x0u},
    {0x80039140u, func_80039140, 0x00000000u, 0x0u},
    {0x800391E4u, func_800391E4, 0x00000000u, 0x0u},
    {0x800393B0u, TextBox_BuildStep, 0x00000000u, 0x0u},
    {0x80039794u, func_80039794, 0x00000000u, 0x0u},
    {0x80039934u, TextBox_SetPos, 0x00000000u, 0x0u},
    {0x80039A14u, func_80039A14, 0x00000000u, 0x0u},
    {0x80039A60u, func_80039A60, 0x00000000u, 0x0u},
    {0x80039AACu, DisplayObjectFade_MarkInitialized, 0x00000000u, 0x0u},
    {0x80039AD4u, DisplayObjectFade_ReleaseChannel, 0x00000000u, 0x0u},
    {0x80039AFCu, func_80039AFC, 0x00000000u, 0x0u},
    {0x80039BE0u, func_80039BE0, 0x00000000u, 0x0u},
    {0x80039C94u, func_80039C94, 0x00000000u, 0x0u},
    {0x80039D64u, DuelEffect_ProcessEntries, 0x00000000u, 0x0u},
    {0x80039E9Cu, func_80039E9C, 0x00000000u, 0x0u},
    {0x80039F1Cu, func_80039F1C, 0x00000000u, 0x0u},
    {0x80039F44u, func_80039F44, 0x00000000u, 0x0u},
    {0x80039F90u, func_80039F90, 0x00000000u, 0x0u},
    {0x80039FD4u, func_80039FD4, 0x00000000u, 0x0u},
    {0x80039FF8u, func_80039FF8, 0x00000000u, 0x0u},
    {0x8003A01Cu, DisplayEffect_LoadResourceStage, 0x00000000u, 0x0u},
    {0x8003A198u, DisplayEffect_HasResourceEntry, 0x00000000u, 0x0u},
    {0x8003A1ECu, DisplayEffect_BuildResourceObjects, 0x00000000u, 0x0u},
    {0x8003A440u, func_8003A440, 0x00000000u, 0x0u},
    {0x8003A560u, func_8003A560, 0x00000000u, 0x0u},
    {0x8003A920u, func_8003A920, 0x00000000u, 0x0u},
    {0x8003A95Cu, DisplayPositionGroup_SetPosition, 0x00000000u, 0x0u},
    {0x8003A990u, func_8003A990, 0x00000000u, 0x0u},
    {0x8003AAE4u, func_8003AAE4, 0x00000000u, 0x0u},
    {0x8003AC48u, func_8003AC48, 0x00000000u, 0x0u},
    {0x8003AD6Cu, func_8003AD6C, 0x00000000u, 0x0u},
    {0x8003B054u, func_8003B054, 0x00000000u, 0x0u},
    {0x8003B378u, DisplayEffect_UpdateMenuRecord, 0x00000000u, 0x0u},
    {0x8003B50Cu, DisplayEffect_ProcessMenuRecords, 0x00000000u, 0x0u},
    {0x8003B5C8u, Text_InitDecimalDigitGlyphMap, 0x00000000u, 0x0u},
    {0x8003B6ACu, DuelEffect_SetEntryRangeLayout, 0x00000000u, 0x0u},
    {0x8003B714u, DuelEffect_InitEntryDefaultFlags, 0x00000000u, 0x0u},
    {0x8003B734u, Input_IsPad1ConfirmPressed, 0x00000000u, 0x0u},
    {0x8003B744u, Text_LookupString, 0x00000000u, 0x0u},
    {0x8003B7E0u, TextStream_ReadByte, 0x00000000u, 0x0u},
    {0x8003B808u, FreeDuel_LoadPackageStage, 0x00000000u, 0x0u},
    {0x8003B9BCu, Main_InitFreeDuelMenu, 0x00000000u, 0x0u},
    {0x8003BA14u, NameEntry_LoadPackageStage, 0x00000000u, 0x0u},
    {0x8003BBF8u, File_RequestNameEntryPackage, 0x00000000u, 0x0u},
    {0x8003BC40u, Text_SjisToGlyphCodes, 0x00000000u, 0x0u},
    {0x8003BD14u, Password_LoadPackageStage, 0x00000000u, 0x0u},
    {0x8003BEB8u, File_RequestPasswordPackage, 0x00000000u, 0x0u},
    {0x8003BF00u, CampaignMap_LoadPackageStage, 0x00000000u, 0x0u},
    {0x8003C0C0u, File_RequestEgyptOverworldPackage, 0x00000000u, 0x0u},
    {0x8003C120u, Options_LoadPackageStage, 0x00000000u, 0x0u},
    {0x8003C2B4u, File_RequestOptionsPackage, 0x00000000u, 0x0u},
    {0x8003C328u, GameOver_LoadPackageStage, 0x00000000u, 0x0u},
    {0x8003C498u, File_RequestGameOverPackage, 0x00000000u, 0x0u},
    {0x8003C4E0u, Options_InitTextDisplay, 0x00000000u, 0x0u},
    {0x8003C568u, Options_UpdateLayout, 0x00000000u, 0x0u},
    {0x8003C628u, Options_Init, 0x00000000u, 0x0u},
    {0x8003C7A0u, Options_HandleInput, 0x00000000u, 0x0u},
    {0x8003C8CCu, Options_Update, 0x00000000u, 0x0u},
    {0x8003C950u, GameOver_Init, 0x00000000u, 0x0u},
    {0x8003CA5Cu, func_8003CA5C, 0x00000000u, 0x0u},
    {0x8003CB7Cu, Input_ResetPads, 0x00000000u, 0x0u},
    {0x8003CBE8u, Input_InitPads, 0x00000000u, 0x0u},
    {0x8003CC38u, Input_ReadRawPads, 0x00000000u, 0x0u},
    {0x8003CCD8u, Input_UpdatePads, 0x00000000u, 0x0u},
    {0x8003CDF8u, Input_BackupPad1AndUsePad2, 0x00000000u, 0x0u},
    {0x8003CE48u, Input_RestorePad1FromBackup, 0x00000000u, 0x0u},
    {0x8003CE74u, SaveData_NextMaskWord, 0x00000000u, 0x0u},
    {0x8003CEB8u, SaveData_CalcCrc16, 0x00000000u, 0x0u},
    {0x8003CF14u, SaveData_WritePrimarySecondaryIntegrity, 0x00000000u, 0x0u},
    {0x8003CFC8u, SaveData_WriteTertiaryIntegrity, 0x00000000u, 0x0u},
    {0x8003D03Cu, SaveData_BuildPayload, 0x00000000u, 0x0u},
    {0x8003D0F4u, SaveData_ApplyRuntimeState, 0x00000000u, 0x0u},
    {0x8003D174u, SaveData_ValidateIntegrity, 0x00000000u, 0x0u},
    {0x8003D288u, SaveData_HasSameDuelistCode, 0x00000000u, 0x0u},
    {0x8003D2B8u, SaveData_MatchesDuelistAndCurrentSequence, 0x00000000u, 0x0u},
    {0x8003D300u, func_8003D300, 0x00000000u, 0x0u},
    {0x8003D32Cu, func_8003D32C, 0x00000000u, 0x0u},
    {0x8003D334u, Checkerboard_DrawBackground, 0x00000000u, 0x0u},
    {0x8003D46Cu, DuelEffect_CreateChannel, 0x00000000u, 0x0u},
    {0x8003D518u, func_8003D518, 0x00000000u, 0x0u},
    {0x8003D614u, func_8003D614, 0x00000000u, 0x0u},
    {0x8003D74Cu, func_8003D74C, 0x00000000u, 0x0u},
    {0x8003DA40u, func_8003DA40, 0x00000000u, 0x0u},
    {0x8003DC1Cu, func_8003DC1C, 0x00000000u, 0x0u},
    {0x8003E46Cu, MemCardDialog_SetMessage, 0x00000000u, 0x0u},
    {0x8003E490u, MemCardDialog_UpdateLoad, 0x00000000u, 0x0u},
    {0x8003E7D4u, MemCardDialog_StepLoad, 0x00000000u, 0x0u},
    {0x8003E80Cu, MemCardDialog_StepLoadUnprompted, 0x00000000u, 0x0u},
    {0x8003E854u, MemCardDialog_UpdateSave, 0x00000000u, 0x0u},
    {0x8003EE90u, MemCardDialog_StepSave, 0x00000000u, 0x0u},
    {0x8003EEC8u, MemCardDialog_StepNone, 0x00000000u, 0x0u},
    {0x8003EED0u, MemCardDialog_UpdateTradeSave, 0x00000000u, 0x0u},
    {0x8003F2B0u, MemCardDialog_StepSlide, 0x00000000u, 0x0u},
    {0x8003F388u, MemCardDialog_CreateObject, 0x00000000u, 0x0u},
    {0x8003F454u, MemCardDialog_Update, 0x00000000u, 0x0u},
    {0x8003F70Cu, MemCardDialog_Poll, 0x00000000u, 0x0u},
    {0x8003F740u, MemCardDialog_Start, 0x00000000u, 0x0u},
    {0x8003F758u, MemCardDialog_Request, 0x00000000u, 0x0u},
    {0x8003F7D4u, SaveData_RequestLoad, 0x00000000u, 0x0u},
    {0x8003F810u, SaveData_PollLoad, 0x00000000u, 0x0u},
    {0x8003F87Cu, SaveData_RequestWrite, 0x00000000u, 0x0u},
    {0x8003F8D4u, SaveData_UpdateLoadPair, 0x00000000u, 0x0u},
    {0x8003FCD8u, SaveData_UpdateTradeLoad, 0x00000000u, 0x0u},
    {0x8003FD14u, SaveData_UpdateDuelLoad, 0x00000000u, 0x0u},
    {0x8003FE14u, SaveData_RequestTradeWrite, 0x00000000u, 0x0u},
    {0x8003FE70u, SaveData_SetMaskSeed, 0x00000000u, 0x0u},
    {0x8003FE80u, Sound_InitFrontend, 0x00000000u, 0x0u},
    {0x8003FEE0u, SD_SEPlayFull, 0x00000000u, 0x0u},
    {0x8003FF08u, SD_BGMPlay, 0x00000000u, 0x0u},
    {0x8003FF34u, SD_BGMFadeOut, 0x00000000u, 0x0u},
    {0x8003FF58u, SD_BGMFadeOutWithStep, 0x00000000u, 0x0u},
    {0x8003FF88u, func_8003FF88, 0x00000000u, 0x0u},
    {0x8003FFB4u, func_8003FFB4, 0x00000000u, 0x0u},
    {0x8003FFD8u, func_8003FFD8, 0x00000000u, 0x0u},
    {0x8003FFFCu, SD_StopAll, 0x00000000u, 0x0u},
    {0x8004002Cu, DisplayObject_FindFreeGeneralSlot, 0x00000000u, 0x0u},
    {0x8004006Cu, DisplayObject_FindFreeSlot, 0x00000000u, 0x0u},
    {0x800400ACu, DisplayObject_AcquireSlot, 0x00000000u, 0x0u},
    {0x8004020Cu, DisplayObject_Release, 0x00000000u, 0x0u},
    {0x800402A0u, DisplayObject_MoveToListHead, 0x00000000u, 0x0u},
    {0x8004036Cu, DisplayObject_ReleaseIfPresent, 0x00000000u, 0x0u},
    {0x80040390u, DisplayObject_ResetPool, 0x00000000u, 0x0u},
    {0x800403F0u, DisplayObject_Reset, 0x00000000u, 0x0u},
    {0x80040410u, DisplayObject_SetResourceVariant, 0x00000000u, 0x0u},
    {0x80040424u, DisplayObject_UpdateResourceVariant, 0x00000000u, 0x0u},
    {0x8004044Cu, DisplayObject_SetResourcePath, 0x00000000u, 0x0u},
    {0x80040468u, DisplayObject_ConfigureSpriteResource, 0x00000000u, 0x0u},
    {0x800404CCu, DisplayObject_ConfigureSpriteAtPosition, 0x00000000u, 0x0u},
    {0x80040510u, DisplayObject_ConfigureScreenSprite, 0x00000000u, 0x0u},
    {0x80040588u, DisplayObject_RenderSpriteList, 0x00000000u, 0x0u},
    {0x80040814u, DisplayObject_RenderSpriteSheetList, 0x00000000u, 0x0u},
    {0x800408D0u, DisplayObject_RenderSpriteStrips, 0x00000000u, 0x0u},
    {0x80040BF8u, DisplayObject_RenderSpriteStripList, 0x00000000u, 0x0u},
    {0x80040CACu, DisplayObject_RunUpdateCallbackList, 0x00000000u, 0x0u},
    {0x80040D14u, DisplayObject_RunSecondaryCallbackList, 0x00000000u, 0x0u},
    {0x80040DD8u, DisplayObject_RenderGouraudQuadList, 0x00000000u, 0x0u},
    {0x80041068u, DisplayObject_RenderTexturedGouraudQuadList, 0x00000000u, 0x0u},
    {0x80041340u, DisplayObject_RenderFrame, 0x00000000u, 0x0u},
    {0x8004141Cu, DisplayObjectStream_Stop, 0x00000000u, 0x0u},
    {0x80041428u, DisplayObjectStream_ResetOffset, 0x00000000u, 0x0u},
    {0x80041434u, DisplayObjectStream_Noop, 0x00000000u, 0x0u},
    {0x8004143Cu, DisplayObjectStream_JumpToOffset, 0x00000000u, 0x0u},
    {0x80041464u, DisplayObjectStream_ToggleFlagAndJumpToOffset, 0x00000000u, 0x0u},
    {0x8004149Cu, DisplayObjectStream_JumpToRandomOffset, 0x00000000u, 0x0u},
    {0x80041534u, DisplayObjectStream_ConfigureRotation, 0x00000000u, 0x0u},
    {0x8004158Cu, DisplayObject_RenderSpriteSheet, 0x00000000u, 0x0u},
    {0x80041C8Cu, DisplayObjectStream_ReadNextCommand, 0x00000000u, 0x0u},
    {0x80041D60u, DisplayObject_UpdateCommandStream, 0x00000000u, 0x0u},
    {0x80041E7Cu, func_80041E7C, 0x00000000u, 0x0u},
    {0x80041F90u, func_80041F90, 0x00000000u, 0x0u},
    {0x80042188u, DisplayObject_SubmitPacket, 0x00000000u, 0x0u},
    {0x800427DCu, DisplayObject_InitializeGouraudQuad, 0x00000000u, 0x0u},
    {0x80042824u, DisplayObject_InitializeTexturedGouraudQuad, 0x00000000u, 0x0u},
    {0x80042874u, DisplayObject_ConfigureSpriteWithResource, 0x00000000u, 0x0u},
    {0x800428A8u, DisplayObject_ConfigureSpriteAtPositionWithResource, 0x00000000u, 0x0u},
    {0x800428ECu, DisplayObject_SetDepthOffset, 0x00000000u, 0x0u},
    {0x80042918u, DisplayObject_SelectOrderingTable1, 0x00000000u, 0x0u},
    {0x8004293Cu, DisplayObject_SelectOrderingTable3, 0x00000000u, 0x0u},
    {0x80042960u, DisplayObject_RunUpdateAndCheckRenderable, 0x00000000u, 0x0u},
    {0x800429A8u, DisplayObjectStream_ReadU16LE, 0x00000000u, 0x0u},
    {0x800429BCu, DisplayObjectStream_ResolveOffset, 0x00000000u, 0x0u},
    {0x800429D8u, DisplayObject_ResetVelocity, 0x00000000u, 0x0u},
    {0x80042A00u, DisplayObject_StepPositionX, 0x00000000u, 0x0u},
    {0x80042A28u, DisplayObject_StepPositionY, 0x00000000u, 0x0u},
    {0x80042A50u, DisplayObject_StepPositionZ, 0x00000000u, 0x0u},
    {0x80042A78u, DisplayObject_StepPositionXY, 0x00000000u, 0x0u},
    {0x80042AA4u, DisplayObject_StepPositionXYZ, 0x00000000u, 0x0u},
    {0x80042AD8u, DisplayObject_StepToward, 0x00000000u, 0x0u},
    {0x80042B08u, DisplayObject_StepTowardZero, 0x00000000u, 0x0u},
    {0x80042B40u, DisplayObject_FindAllocatedByTag, 0x00000000u, 0x0u},
    {0x80042B98u, DisplayObject_MarkInitialized, 0x00000000u, 0x0u},
    {0x80042BC0u, DisplayObject_FadeBrightnessAndRelease, 0x00000000u, 0x0u},
    {0x80042C08u, DisplayObject_RenderSpotlightMask, 0x00000000u, 0x0u},
    {0x80043178u, DisplayObject_SavePosition, 0x00000000u, 0x0u},
    {0x8004318Cu, DisplayObject_InterpolatePositionCosine, 0x00000000u, 0x0u},
    {0x80043230u, Widget_SlideSine, 0x00000000u, 0x0u},
    {0x80043328u, Main_LoadBootPackageStage, 0x00000000u, 0x0u},
    {0x800434F4u, Main_LoadBootImageStage, 0x00000000u, 0x0u},
    {0x8004365Cu, func_8004365C, 0x00000000u, 0x0u},
    {0x800438B8u, Main_HoldBootScreen, 0x00000000u, 0x0u},
    {0x80043960u, Main_RunBootSequence, 0x00000000u, 0x0u},
    {0x80043BCCu, Main_RunFrontendLoop, 0x00000000u, 0x0u},
    {0x80043D48u, MemCard_ClearIOEvents, 0x00000000u, 0x0u},
    {0x80043DA0u, MemCard_WaitIOEvent, 0x00000000u, 0x0u},
    {0x80043E30u, MemCard_Init, 0x00000000u, 0x0u},
    {0x80043E68u, MemCard_CloseIOEvents, 0x00000000u, 0x0u},
    {0x80043EBCu, MemCard_InitIOEvents, 0x00000000u, 0x0u},
    {0x80044038u, MemCard_ClearCard, 0x00000000u, 0x0u},
    {0x800440B4u, MemCard_BeginRequest, 0x00000000u, 0x0u},
    {0x800440F0u, MemCard_ReqCardInfo, 0x00000000u, 0x0u},
    {0x8004413Cu, MemCard_ReqLoadDirectory, 0x00000000u, 0x0u},
    {0x800441DCu, MemCard_ReqReadFile, 0x00000000u, 0x0u},
    {0x80044278u, MemCard_ReqReadSector, 0x00000000u, 0x0u},
    {0x800442E4u, MemCard_ReqWriteFile, 0x00000000u, 0x0u},
    {0x80044380u, MemCard_ReqWriteSector, 0x00000000u, 0x0u},
    {0x800443ECu, MemCard_ReqCreateFile, 0x00000000u, 0x0u},
    {0x80044470u, MemCard_FindFiles, 0x00000000u, 0x0u},
    {0x80044544u, MemCard_CalcFreeBlocks, 0x00000000u, 0x0u},
    {0x80044598u, MemCard_FindEntry, 0x00000000u, 0x0u},
    {0x80044608u, MemCard_DoLoadDirectory, 0x00000000u, 0x0u},
    {0x80044838u, MemCard_ProcessRequest, 0x00000000u, 0x0u},
    {0x80044CD4u, MemCard_FindLoadedEntry, 0x00000000u, 0x0u},
    {0x80044CFCu, MemCard_SetIOResultCompleteCB, 0x00000000u, 0x0u},
    {0x80044D0Cu, MemCard_SetIOResultTimeoutCB, 0x00000000u, 0x0u},
    {0x80044D20u, MemCard_SetIOResultErrorCB, 0x00000000u, 0x0u},
    {0x80044D34u, MemCard_SetIOResultNewCardCB, 0x00000000u, 0x0u},
    {0x80044D48u, SD_InitBufferState, 0x00000000u, 0x0u},
    {0x80044DA0u, SD_ResetCdPan, 0x00000000u, 0x0u},
    {0x80044DC0u, func_80044DC0, 0x00000000u, 0x0u},
    {0x80044E90u, SD_SetCdPan, 0x00000000u, 0x0u},
    {0x80044F58u, func_80044F58, 0x00000000u, 0x0u},
    {0x80044FE4u, SD_GetCdVolume, 0x00000000u, 0x0u},
    {0x80044FFCu, func_80044FFC, 0x00000000u, 0x0u},
    {0x8004503Cu, func_8004503C, 0x00000000u, 0x0u},
    {0x80045054u, func_80045054, 0x00000000u, 0x0u},
    {0x80045114u, func_80045114, 0x00000000u, 0x0u},
    {0x800451E0u, func_800451E0, 0x00000000u, 0x0u},
    {0x80045208u, func_80045208, 0x00000000u, 0x0u},
    {0x80045334u, func_80045334, 0x00000000u, 0x0u},
    {0x8004544Cu, SD_ClearBusyFlag, 0x00000000u, 0x0u},
    {0x8004545Cu, SD_ArmBusyCallback, 0x00000000u, 0x0u},
    {0x80045484u, SD_HasQueuedStreamCommand, 0x00000000u, 0x0u},
    {0x80045514u, func_80045514, 0x00000000u, 0x0u},
    {0x80045BE8u, SD_EnqueueCommand, 0x00000000u, 0x0u},
    {0x80045C98u, SD_UpdateFades, 0x00000000u, 0x0u},
    {0x80045F3Cu, SD_UpdateRuntime, 0x00000000u, 0x0u},
    {0x80046294u, func_80046294, 0x00000000u, 0x0u},
    {0x800464F0u, func_800464F0, 0x00000000u, 0x0u},
    {0x8004666Cu, func_8004666C, 0x00000000u, 0x0u},
    {0x800466C8u, func_800466C8, 0x00000000u, 0x0u},
    {0x8004671Cu, func_8004671C, 0x00000000u, 0x0u},
    {0x80046768u, SD_InitState, 0x00000000u, 0x0u},
    {0x8004695Cu, SD_SetSequenceVSyncMode, 0x00000000u, 0x0u},
    {0x80046990u, SD_InitDataSourceFlags, 0x00000000u, 0x0u},
    {0x80046A08u, func_80046A08, 0x00000000u, 0x0u},
    {0x80046DE8u, SD_ResetRuntime, 0x00000000u, 0x0u},
    {0x80046F58u, SD_Shutdown, 0x00000000u, 0x0u},
    {0x80046FA0u, SD_SetOutputType, 0x00000000u, 0x0u},
    {0x80047008u, SD_GetOutputType, 0x00000000u, 0x0u},
    {0x8004701Cu, func_8004701C, 0x00000000u, 0x0u},
    {0x8004703Cu, SD_GetStatusFlags, 0x00000000u, 0x0u},
    {0x80047050u, SD_VSync, 0x00000000u, 0x0u},
    {0x800470B0u, func_800470B0, 0x00000000u, 0x0u},
    {0x80047140u, func_80047140, 0x00000000u, 0x0u},
    {0x800471D0u, func_800471D0, 0x00000000u, 0x0u},
    {0x80047278u, func_80047278, 0x00000000u, 0x0u},
    {0x800472A8u, func_800472A8, 0x00000000u, 0x0u},
    {0x80047314u, func_80047314, 0x00000000u, 0x0u},
    {0x8004733Cu, func_8004733C, 0x00000000u, 0x0u},
    {0x800473CCu, func_800473CC, 0x00000000u, 0x0u},
    {0x800473F0u, func_800473F0, 0x00000000u, 0x0u},
    {0x80047430u, func_80047430, 0x00000000u, 0x0u},
    {0x80047458u, func_80047458, 0x00000000u, 0x0u},
    {0x80047480u, SD_InitVoiceState, 0x00000000u, 0x0u},
    {0x8004763Cu, func_8004763C, 0x00000000u, 0x0u},
    {0x800476B4u, func_800476B4, 0x00000000u, 0x0u},
    {0x80047788u, SD_QueueValueLinkTransfer, 0x00000000u, 0x0u},
    {0x80047864u, SD_ApplyVoiceSlotVolume, 0x00000000u, 0x0u},
    {0x800478ECu, SD_UpdateVoiceSlots, 0x00000000u, 0x0u},
    {0x80047A68u, func_80047A68, 0x00000000u, 0x0u},
    {0x80047AD0u, func_80047AD0, 0x00000000u, 0x0u},
    {0x80047B68u, SD_RequestValueLink, 0x00000000u, 0x0u},
    {0x80047BB4u, func_80047BB4, 0x00000000u, 0x0u},
    {0x80047C50u, func_80047C50, 0x00000000u, 0x0u},
    {0x80047C70u, SD_KeyOffVoice, 0x00000000u, 0x0u},
    {0x80047CC4u, func_80047CC4, 0x00000000u, 0x0u},
    {0x80047DB0u, SD_SEStop, 0x00000000u, 0x0u},
    {0x80047EC4u, SD_KeyOffVoiceSlots, 0x00000000u, 0x0u},
    {0x80047F38u, func_80047F38, 0x00000000u, 0x0u},
    {0x80047FACu, func_80047FAC, 0x00000000u, 0x0u},
    {0x8004803Cu, func_8004803C, 0x00000000u, 0x0u},
    {0x800482B0u, func_800482B0, 0x00000000u, 0x0u},
    {0x80048658u, SD_SEPlay, 0x00000000u, 0x0u},
    {0x80048768u, func_80048768, 0x00000000u, 0x0u},
    {0x80048920u, SD_SESetVolume, 0x00000000u, 0x0u},
    {0x80048A28u, func_80048A28, 0x00000000u, 0x0u},
    {0x80048C0Cu, func_80048C0C, 0x00000000u, 0x0u},
    {0x80048C70u, func_80048C70, 0x00000000u, 0x0u},
    {0x80048D08u, SD_LoadSequenceBankPair, 0x00000000u, 0x0u},
    {0x80048F14u, SD_InitSecondaryRuntime, 0x00000000u, 0x0u},
    {0x80049010u, SD_ResetMusicState, 0x00000000u, 0x0u},
    {0x800490F0u, func_800490F0, 0x00000000u, 0x0u},
    {0x80049108u, func_80049108, 0x00000000u, 0x0u},
    {0x80049120u, SD_IsBgmFadeActive, 0x00000000u, 0x0u},
    {0x80049138u, SD_RequestMusicPackageLoad, 0x00000000u, 0x0u},
    {0x80049200u, SD_RequestBgmPlaybackDefaultStep, 0x00000000u, 0x0u},
    {0x80049230u, SD_RequestBgmPlayback, 0x00000000u, 0x0u},
    {0x800492D8u, SD_Init, 0x00000000u, 0x0u},
    {0x80049308u, SD_OpenMusicVab, 0x00000000u, 0x0u},
    {0x80049394u, SD_SetMusicTrackBuffer, 0x00000000u, 0x0u},
    {0x800493F8u, SD_ResetMusicTrackBuffer, 0x00000000u, 0x0u},
    {0x80049434u, SD_ResetSecondaryState, 0x00000000u, 0x0u},
    {0x800494F4u, SD_InitSecondaryWorkArea, 0x00000000u, 0x0u},
    {0x80049544u, SD_EnableSecondarySequenceUpdates, 0x00000000u, 0x0u},
    {0x80049594u, SD_SetSequenceTickMode, 0x00000000u, 0x0u},
    {0x800495A4u, SD_UpdateSecondarySequenceIfEnabled, 0x00000000u, 0x0u},
    {0x800495DCu, SD_EnableSecondaryPanning, 0x00000000u, 0x0u},
    {0x800495ECu, SD_DisableSecondaryPanning, 0x00000000u, 0x0u},
    {0x80049600u, SD_SetSecondaryObjectCount, 0x00000000u, 0x0u},
    {0x80049640u, SD_ResetSecondaryRuntime, 0x00000000u, 0x0u},
    {0x80049694u, SD_Term, 0x00000000u, 0x0u},
    {0x800496C4u, SD_VabOpenHead, 0x00000000u, 0x0u},
    {0x8004975Cu, SD_VabTransBody, 0x00000000u, 0x0u},
    {0x800497E0u, SD_VabTransBodyChunk, 0x00000000u, 0x0u},
    {0x800498BCu, SD_VabTransCompleted, 0x00000000u, 0x0u},
    {0x800498F8u, SD_ResetVabTransferState, 0x00000000u, 0x0u},
    {0x80049920u, func_80049920, 0x00000000u, 0x0u},
    {0x80049A64u, SD_OpenSequence, 0x00000000u, 0x0u},
    {0x80049AF4u, SD_PlaySequence, 0x00000000u, 0x0u},
    {0x80049BACu, SD_PlaySequenceFastForward, 0x00000000u, 0x0u},
    {0x80049C40u, SD_StopSequence, 0x00000000u, 0x0u},
    {0x80049CB0u, func_80049CB0, 0x00000000u, 0x0u},
    {0x80049CF8u, SD_MuteSecondaryVoices, 0x00000000u, 0x0u},
    {0x80049DD8u, SD_RestoreSecondaryVoiceVolumes, 0x00000000u, 0x0u},
    {0x80049EC8u, SD_SetSecondarySpatialLevels, 0x00000000u, 0x0u},
    {0x80049F10u, SD_SetSecondaryMasterLevels, 0x00000000u, 0x0u},
    {0x80049F50u, SD_PollSequenceState, 0x00000000u, 0x0u},
    {0x80049FB4u, func_80049FB4, 0x00000000u, 0x0u},
    {0x8004A0FCu, SD_SpatializeSecondaryObject, 0x00000000u, 0x0u},
    {0x8004A27Cu, SD_SetVoiceVolume, 0x00000000u, 0x0u},
    {0x8004A2F8u, SD_UpdateSecondaryObjectVolumes, 0x00000000u, 0x0u},
    {0x8004A3BCu, SD_CalcPitchBend, 0x00000000u, 0x0u},
    {0x8004A43Cu, func_8004A43C, 0x00000000u, 0x0u},
    {0x8004A518u, SD_ResetSecondaryPlayback, 0x00000000u, 0x0u},
    {0x8004A6D8u, func_8004A6D8, 0x00000000u, 0x0u},
    {0x8004A6F8u, SD_SetVoiceEnvelopeFromTone, 0x00000000u, 0x0u},
    {0x8004A764u, SD_ResetVoiceEnvelope, 0x00000000u, 0x0u},
    {0x8004A7C0u, func_8004A7C0, 0x00000000u, 0x0u},
    {0x8004A854u, SD_FindLowestPrioritySecondaryObject, 0x00000000u, 0x0u},
    {0x8004A8E4u, SD_PrepareSecondaryObjectReuse, 0x00000000u, 0x0u},
    {0x8004A940u, SD_SelectSecondaryObject, 0x00000000u, 0x0u},
    {0x8004AAFCu, func_8004AAFC, 0x00000000u, 0x0u},
    {0x8004ACE4u, func_8004ACE4, 0x00000000u, 0x0u},
    {0x8004ADE8u, func_8004ADE8, 0x00000000u, 0x0u},
    {0x8004B374u, func_8004B374, 0x00000000u, 0x0u},
    {0x8004B49Cu, func_8004B49C, 0x00000000u, 0x0u},
    {0x8004B6E8u, SD_SetSequenceChannelProgram, 0x00000000u, 0x0u},
    {0x8004B70Cu, func_8004B70C, 0x00000000u, 0x0u},
    {0x8004B734u, SD_SequenceTimerCallback, 0x00000000u, 0x0u},
    {0x8004B854u, SD_OpenSequenceTimerEvent, 0x00000000u, 0x0u},
    {0x8004B910u, SD_CloseSequenceTimerEvent, 0x00000000u, 0x0u},
    {0x8004B990u, SD_StopSequenceTimer, 0x00000000u, 0x0u},
    {0x8004B9E0u, SD_UpdateSecondarySequence, 0x00000000u, 0x0u},
    {0x8004BAA0u, SD_CompareBytes, 0x00000000u, 0x0u},
    {0x8004BAE4u, SD_ReadSequenceByte, 0x00000000u, 0x0u},
    {0x8004BB34u, SD_ReadVariableLengthValue, 0x00000000u, 0x0u},
    {0x8004BBBCu, SD_FindMidiTrackChunk, 0x00000000u, 0x0u},
    {0x8004BC2Cu, SD_ReadSequenceU32BE, 0x00000000u, 0x0u},
    {0x8004BCA8u, SD_ReadSequenceU16BE, 0x00000000u, 0x0u},
    {0x8004BCE8u, SD_ReadSequenceHeader, 0x00000000u, 0x0u},
    {0x8004BE6Cu, SD_AdvanceSequencePosition, 0x00000000u, 0x0u},
    {0x8004BE80u, SD_IgnoreSequenceEvent, 0x00000000u, 0x0u},
    {0x8004BE88u, SD_HandleSequenceMetaEvent, 0x00000000u, 0x0u},
    {0x8004C0ACu, SD_SkipSequenceSysEx, 0x00000000u, 0x0u},
    {0x8004C114u, SD_DispatchSequenceChannelEvent, 0x00000000u, 0x0u},
    {0x8004C420u, SD_ReadSequenceEvent, 0x00000000u, 0x0u},
    {0x8004C560u, SD_OpenSequenceTrack, 0x00000000u, 0x0u},
    {0x8004C5C8u, SD_ScaleSequenceDelta, 0x00000000u, 0x0u},
    {0x8004C77Cu, SD_StartSequenceTracks, 0x00000000u, 0x0u},
    {0x8004C84Cu, func_8004C84C, 0x00000000u, 0x0u},
    {0x8004C8C8u, SD_ProcessSequenceTracks, 0x00000000u, 0x0u},
    {0x8004CA60u, SD_ResetSequenceTracks, 0x00000000u, 0x0u},
    {0x8004CABCu, SD_GetSequenceStatus, 0x00000000u, 0x0u},
    {0x8004CB0Cu, func_8004CB0C, 0x00000000u, 0x0u},
    {0x8004D134u, func_8004D134, 0x00000000u, 0x0u},
    {0x8004D58Cu, func_8004D58C, 0x00000000u, 0x0u},
    {0x8004D75Cu, func_8004D75C, 0x00000000u, 0x0u},
    {0x8004D914u, func_8004D914, 0x00000000u, 0x0u},
    {0x8004DB14u, func_8004DB14, 0x00000000u, 0x0u},
    {0x8004DC38u, func_8004DC38, 0x00000000u, 0x0u},
    {0x8004DE24u, func_8004DE24, 0x00000000u, 0x0u},
    {0x8004E7B0u, func_8004E7B0, 0x00000000u, 0x0u},
    {0x8004E9A0u, func_8004E9A0, 0x00000000u, 0x0u},
    {0x8004EB00u, func_8004EB00, 0x00000000u, 0x0u},
    {0x8004FE2Cu, func_8004FE2C, 0x00000000u, 0x0u},
    {0x80050584u, func_80050584, 0x00000000u, 0x0u},
    {0x800507D0u, func_800507D0, 0x00000000u, 0x0u},
    {0x80050F24u, func_80050F24, 0x00000000u, 0x0u},
    {0x8005106Cu, func_8005106C, 0x00000000u, 0x0u},
    {0x80051350u, func_80051350, 0x00000000u, 0x0u},
    {0x80051A48u, func_80051A48, 0x00000000u, 0x0u},
    {0x80052528u, func_80052528, 0x00000000u, 0x0u},
    {0x80052694u, func_80052694, 0x00000000u, 0x0u},
    {0x800528ACu, func_800528AC, 0x00000000u, 0x0u},
    {0x80052D2Cu, func_80052D2C, 0x00000000u, 0x0u},
    {0x800530C4u, func_800530C4, 0x00000000u, 0x0u},
    {0x80053248u, Model_SetSlotProperties, 0x00000000u, 0x0u},
    {0x800533D8u, func_800533D8, 0x00000000u, 0x0u},
    {0x800534B8u, ModelDebug_UpdateController, 0x00000000u, 0x0u},
    {0x800540B4u, func_800540B4, 0x00000000u, 0x0u},
    {0x800556E8u, func_800556E8, 0x00000000u, 0x0u},
    {0x800559D4u, func_800559D4, 0x00000000u, 0x0u},
    {0x8005611Cu, func_8005611C, 0x00000000u, 0x0u},
    {0x80056250u, func_80056250, 0x00000000u, 0x0u},
    {0x80056504u, Model_LoadMonsterMerge, 0x00000000u, 0x0u},
    {0x80056828u, func_80056828, 0x00000000u, 0x0u},
    {0x80056D7Cu, func_80056D7C, 0x00000000u, 0x0u},
    {0x80057544u, func_80057544, 0x00000000u, 0x0u},
    {0x800577B0u, func_800577B0, 0x00000000u, 0x0u},
    {0x80057AF4u, Model_ControlSlotAnimation, 0x00000000u, 0x0u},
    {0x80057E20u, func_80057E20, 0x00000000u, 0x0u},
    {0x80057F38u, Model_UpdateViewMetrics, 0x00000000u, 0x0u},
    {0x800580D4u, func_800580D4, 0x00000000u, 0x0u},
    {0x800582C0u, Model_ApplyTextureTint, 0x00000000u, 0x0u},
    {0x80058434u, func_80058434, 0x00000000u, 0x0u},
    {0x80058624u, SD_ApplyPositionalSound, 0x00000000u, 0x0u},
    {0x80058838u, Model_QueueTintRequestForParts, 0x00000000u, 0x0u},
    {0x80058938u, Model_QueueTintRequest, 0x00000000u, 0x0u},
    {0x80058A7Cu, ModelTexture_PackPageClut, 0x00000000u, 0x0u},
    {0x80058B4Cu, ModelTexture_LoadTim, 0x00000000u, 0x0u},
    {0x80058DC0u, func_80058DC0, 0x00000000u, 0x0u},
    {0x80058DCCu, Model_GetActiveSlotIndex, 0x00000000u, 0x0u},
    {0x80058DD8u, func_80058DD8, 0x00000000u, 0x0u},
    {0x80058E1Cu, Model_GetFrameStep, 0x00000000u, 0x0u},
    {0x80058E3Cu, Model_GetSlotAnimationSpeed, 0x00000000u, 0x0u},
    {0x80058E68u, Model_GetSlotAnimationIndex, 0x00000000u, 0x0u},
    {0x80058E94u, Model_GetSlotAnimationFrame, 0x00000000u, 0x0u},
    {0x80058EC0u, Model_GetSlotAnimationLength, 0x00000000u, 0x0u},
    {0x80058F10u, func_80058F10, 0x00000000u, 0x0u},
    {0x80058F20u, Model_GetSlotDataEntry, 0x00000000u, 0x0u},
    {0x80058F74u, Model_GetCurrentDataEntry, 0x00000000u, 0x0u},
    {0x80058FB0u, Model_CopySlotU16Values, 0x00000000u, 0x0u},
    {0x80059000u, func_80059000, 0x00000000u, 0x0u},
    {0x800590DCu, func_800590DC, 0x00000000u, 0x0u},
    {0x80059134u, Model_InitLightTriplet, 0x00000000u, 0x0u},
    {0x800591C0u, Model_GetFlatLight, 0x00000000u, 0x0u},
    {0x800591FCu, Model_GetCameraViewBuffer, 0x00000000u, 0x0u},
    {0x80059208u, Model_GetViewMetricsBuffer, 0x00000000u, 0x0u},
    {0x80059214u, Model_GetCameraCoordinateUnit, 0x00000000u, 0x0u},
    {0x80059220u, Model_GetLightSourceMatrix, 0x00000000u, 0x0u},
    {0x8005922Cu, func_8005922C, 0x00000000u, 0x0u},
    {0x80059284u, func_80059284, 0x00000000u, 0x0u},
    {0x800592ACu, Model_BuildCameraRelativeCoordinateUnit, 0x00000000u, 0x0u},
    {0x800593D0u, func_800593D0, 0x00000000u, 0x0u},
    {0x8005949Cu, func_8005949C, 0x00000000u, 0x0u},
    {0x800594C0u, func_800594C0, 0x00000000u, 0x0u},
    {0x80059520u, func_80059520, 0x00000000u, 0x0u},
    {0x80059590u, Model_SetSlotTintTarget, 0x00000000u, 0x0u},
    {0x800595C8u, func_800595C8, 0x00000000u, 0x0u},
    {0x8005969Cu, func_8005969C, 0x00000000u, 0x0u},
    {0x80059700u, func_80059700, 0x00000000u, 0x0u},
    {0x800597C8u, func_800597C8, 0x00000000u, 0x0u},
    {0x8005988Cu, HostFile_GetSize, 0x00000000u, 0x0u},
    {0x800598E4u, HostFile_ReadAll, 0x00000000u, 0x0u},
    {0x80059908u, HostFile_ReadRange, 0x00000000u, 0x0u},
    {0x800599FCu, func_800599FC, 0x00000000u, 0x0u},
    {0x80059A50u, func_80059A50, 0x00000000u, 0x0u},
    {0x80059AA8u, Model_SetSlotShadowEnabled, 0x00000000u, 0x0u},
    {0x80059AE0u, Model_SetScreenYOverride, 0x00000000u, 0x0u},
    {0x80059AECu, Model_SetFrameStepOverride, 0x00000000u, 0x0u},
    {0x80059AF8u, func_80059AF8, 0x00000000u, 0x0u},
    {0x80059B90u, func_80059B90, 0x00000000u, 0x0u},
    {0x80059C18u, Model_SetPresentationBgmCommand, 0x00000000u, 0x0u},
    {0x80059C24u, Model_StartExodiaPresentation, 0x00000000u, 0x0u},
    {0x80059C88u, Model_IsExodiaPresentationComplete, 0x00000000u, 0x0u},
    {0x80059C9Cu, Model_StartCreditsPresentation, 0x00000000u, 0x0u},
    {0x80059CD0u, Model_IsCreditsPresentationComplete, 0x00000000u, 0x0u},
    {0x80059CE4u, Model_UpdateScene, 0x00000000u, 0x0u},
    {0x80059DD8u, Model_RunSlotHandlers, 0x00000000u, 0x0u},
    {0x80059EBCu, func_80059EBC, 0x00000000u, 0x0u},
    {0x80059F18u, func_80059F18, 0x00000000u, 0x0u},
    {0x80059FACu, Model_SetCameraEyeSlots, 0x00000000u, 0x0u},
    {0x8005A010u, func_8005A010, 0x00000000u, 0x0u},
    {0x8005A074u, func_8005A074, 0x00000000u, 0x0u},
    {0x8005A0DCu, func_8005A0DC, 0x00000000u, 0x0u},
    {0x8005A130u, func_8005A130, 0x00000000u, 0x0u},
    {0x8005A188u, func_8005A188, 0x00000000u, 0x0u},
    {0x8005A1F4u, Model_GetSlotDistanceFromCameraEye, 0x00000000u, 0x0u},
    {0x8005A2E0u, Model_GetSlotDistanceFromCameraTarget, 0x00000000u, 0x0u},
    {0x8005A3D0u, func_8005A3D0, 0x00000000u, 0x0u},
    {0x8005A468u, func_8005A468, 0x00000000u, 0x0u},
    {0x8005A4C4u, func_8005A4C4, 0x00000000u, 0x0u},
    {0x8005A53Cu, func_8005A53C, 0x00000000u, 0x0u},
    {0x8005A618u, func_8005A618, 0x00000000u, 0x0u},
    {0x8005A6A8u, SD_CalcSpatialVolumePan, 0x00000000u, 0x0u},
    {0x8005A878u, func_8005A878, 0x00000000u, 0x0u},
    {0x8005A8C4u, Model_HasInsufficientBufferSpace, 0x00000000u, 0x0u},
    {0x8005A98Cu, Color_RgbToHsl, 0x00000000u, 0x0u},
    {0x8005ABA0u, Color_HslToRgb, 0x00000000u, 0x0u},
    {0x8005AE68u, Color_TintBgr555Pixel, 0x00000000u, 0x0u},
    {0x8005B054u, func_8005B054, 0x00000000u, 0x0u},
    {0x8005B0B4u, func_8005B0B4, 0x00000000u, 0x0u},
    {0x8005B260u, func_8005B260, 0x00000000u, 0x0u},
    {0x8005B36Cu, Graphics_SubmitTextureWindowPacket, 0x00000000u, 0x0u},
    {0x8005B4D8u, func_8005B4D8, 0x00000000u, 0x0u},
    {0x8005B5FCu, Model_FillWords, 0x00000000u, 0x0u},
    {0x8005B620u, Model_CopyWords, 0x00000000u, 0x0u},
    {0x8005B64Cu, MainMenu_LoadPackageStage, 0x00000000u, 0x0u},
    {0x8005B85Cu, File_RequestMainMenuPackage, 0x00000000u, 0x0u},
    {0x8005B8A0u, func_8005B8A0, 0x00000000u, 0x0u},
    {0x8005BB7Cu, Movie_StopStream, 0x00000000u, 0x0u},
    {0x8005BE3Cu, Movie_DecodeAndPresentFrame, 0x00000000u, 0x0u},
    {0x8005BFC8u, Movie_WaitAndDecodeFrame, 0x00000000u, 0x0u},
    {0x8005C1F4u, func_8005C1F4, 0x00000000u, 0x0u},
    {0x8005C374u, func_8005C374, 0x00000000u, 0x0u},
    {0x8005C388u, func_8005C388, 0x00000000u, 0x0u},
    {0x8005C464u, Movie_StartFileStream, 0x00000000u, 0x0u},
    {0x8005C4F0u, File_Exists, 0x00000000u, 0x0u},
    {0x8005C530u, Movie_StepPlayback, 0x00000000u, 0x0u},
    {0x8005C568u, Movie_MoveDisplayImage, 0x00000000u, 0x0u},
    {0x8005C5C4u, Movie_StartFadeOut, 0x00000000u, 0x0u},
    {0x8005C5D4u, Movie_WaitFrameDecoded, 0x00000000u, 0x0u},
    {0x8005C62Cu, func_8005C62C, 0x00000000u, 0x0u},
    {0x8005C690u, func_8005C690, 0x00000000u, 0x0u},
    {0x8005C6A0u, func_8005C6A0, 0x00000000u, 0x0u},
    {0x8005C768u, func_8005C768, 0x00000000u, 0x0u},
    {0x8005C7BCu, func_8005C7BC, 0x00000000u, 0x0u},
    {0x8005CEF0u, func_8005CEF0, 0x00000000u, 0x0u},
    {0x8005D378u, func_8005D378, 0x00000000u, 0x0u},
    {0x8005D994u, func_8005D994, 0x00000000u, 0x0u},
    {0x8005DBA4u, func_8005DBA4, 0x00000000u, 0x0u},
    {0x8005E808u, func_8005E808, 0x00000000u, 0x0u},
    {0x8005EBF4u, func_8005EBF4, 0x00000000u, 0x0u},
    {0x8005F070u, func_8005F070, 0x00000000u, 0x0u},
    {0x8005F174u, func_8005F174, 0x00000000u, 0x0u},
    {0x8005F180u, func_8005F180, 0x00000000u, 0x0u},
    {0x8005F18Cu, func_8005F18C, 0x00000000u, 0x0u},
    {0x8005F198u, func_8005F198, 0x00000000u, 0x0u},
    {0x8005F1A4u, func_8005F1A4, 0x00000000u, 0x0u},
    {0x8005F1B8u, func_8005F1B8, 0x00000000u, 0x0u},
    {0x8005F27Cu, func_8005F27C, 0x00000000u, 0x0u},
    {0x8005F3B8u, func_8005F3B8, 0x00000000u, 0x0u},
    {0x8005F564u, func_8005F564, 0x00000000u, 0x0u},
    {0x8005F588u, func_8005F588, 0x00000000u, 0x0u},
    {0x8005F5C8u, func_8005F5C8, 0x00000000u, 0x0u},
    {0x8005F714u, func_8005F714, 0x00000000u, 0x0u},
    {0x8005F7B0u, func_8005F7B0, 0x00000000u, 0x0u},
    {0x8005F828u, func_8005F828, 0x00000000u, 0x0u},
    {0x8005F91Cu, func_8005F91C, 0x00000000u, 0x0u},
    {0x8005FAE4u, func_8005FAE4, 0x00000000u, 0x0u},
    {0x8005FB08u, func_8005FB08, 0x00000000u, 0x0u},
    {0x8005FB14u, func_8005FB14, 0x00000000u, 0x0u},
    {0x8005FB30u, func_8005FB30, 0x00000000u, 0x0u},
    {0x8005FBC4u, func_8005FBC4, 0x00000000u, 0x0u},
    {0x8005FC1Cu, func_8005FC1C, 0x00000000u, 0x0u},
    {0x8005FE44u, func_8005FE44, 0x00000000u, 0x0u},
    {0x80060170u, Model_RegisterHandlerKey, 0x00000000u, 0x0u},
    {0x800601D0u, Model_FindHandlerKey, 0x00000000u, 0x0u},
    {0x80060220u, Model_ProcessType2Unit, 0x00000000u, 0x0u},
    {0x800603DCu, func_800603DC, 0x00000000u, 0x0u},
    {0x8006041Cu, Model_GetPrimitiveHandler, 0x00000000u, 0x0u},
    {0x8006086Cu, func_8006086C, 0x00000000u, 0x0u},
    {0x800608B8u, func_800608B8, 0x00000000u, 0x0u},
    {0x80060AECu, func_80060AEC, 0x00000000u, 0x0u},
    {0x80060B38u, CardList_RenderDeckBoxStats, 0x00000000u, 0x0u},
    {0x80060E70u, func_80060E70, 0x00000000u, 0x0u},
    {0x80061008u, func_80061008, 0x00000000u, 0x0u},
    {0x800610E0u, func_800610E0, 0x00000000u, 0x0u},
    {0x800611D0u, func_800611D0, 0x00000000u, 0x0u},
    {0x800612C0u, func_800612C0, 0x00000000u, 0x0u},
    {0x8006151Cu, func_8006151C, 0x00000000u, 0x0u},
    {0x800617E0u, func_800617E0, 0x00000000u, 0x0u},
    {0x80061A84u, func_80061A84, 0x00000000u, 0x0u},
    {0x80061DDCu, func_80061DDC, 0x00000000u, 0x0u},
    {0x80062058u, func_80062058, 0x00000000u, 0x0u},
    {0x8006233Cu, func_8006233C, 0x00000000u, 0x0u},
    {0x80062600u, func_80062600, 0x00000000u, 0x0u},
    {0x80062978u, func_80062978, 0x00000000u, 0x0u},
    {0x80062BC0u, func_80062BC0, 0x00000000u, 0x0u},
    {0x80062E70u, func_80062E70, 0x00000000u, 0x0u},
    {0x80063100u, func_80063100, 0x00000000u, 0x0u},
    {0x80063444u, func_80063444, 0x00000000u, 0x0u},
    {0x800636ACu, func_800636AC, 0x00000000u, 0x0u},
    {0x8006397Cu, func_8006397C, 0x00000000u, 0x0u},
    {0x80063C2Cu, func_80063C2C, 0x00000000u, 0x0u},
    {0x80063F90u, func_80063F90, 0x00000000u, 0x0u},
    {0x80064248u, func_80064248, 0x00000000u, 0x0u},
    {0x80064568u, func_80064568, 0x00000000u, 0x0u},
    {0x80064868u, func_80064868, 0x00000000u, 0x0u},
    {0x80064C1Cu, func_80064C1C, 0x00000000u, 0x0u},
    {0x80064EF4u, func_80064EF4, 0x00000000u, 0x0u},
    {0x80065234u, func_80065234, 0x00000000u, 0x0u},
    {0x80065554u, func_80065554, 0x00000000u, 0x0u},
    {0x80065928u, func_80065928, 0x00000000u, 0x0u},
    {0x80065BCCu, func_80065BCC, 0x00000000u, 0x0u},
    {0x80065ED8u, func_80065ED8, 0x00000000u, 0x0u},
    {0x800661C4u, func_800661C4, 0x00000000u, 0x0u},
    {0x80066564u, func_80066564, 0x00000000u, 0x0u},
    {0x80066828u, func_80066828, 0x00000000u, 0x0u},
    {0x80066B54u, func_80066B54, 0x00000000u, 0x0u},
    {0x80066E60u, func_80066E60, 0x00000000u, 0x0u},
    {0x80067220u, func_80067220, 0x00000000u, 0x0u},
    {0x80067354u, func_80067354, 0x00000000u, 0x0u},
    {0x8006759Cu, func_8006759C, 0x00000000u, 0x0u},
    {0x80067858u, func_80067858, 0x00000000u, 0x0u},
    {0x80067ABCu, func_80067ABC, 0x00000000u, 0x0u},
    {0x80067D94u, func_80067D94, 0x00000000u, 0x0u},
    {0x80067FD0u, func_80067FD0, 0x00000000u, 0x0u},
    {0x8006825Cu, func_8006825C, 0x00000000u, 0x0u},
    {0x800684B4u, func_800684B4, 0x00000000u, 0x0u},
    {0x8006875Cu, func_8006875C, 0x00000000u, 0x0u},
    {0x80068A00u, func_80068A00, 0x00000000u, 0x0u},
    {0x80068D18u, func_80068D18, 0x00000000u, 0x0u},
    {0x80068FD8u, func_80068FD8, 0x00000000u, 0x0u},
    {0x8006930Cu, func_8006930C, 0x00000000u, 0x0u},
    {0x800695A4u, func_800695A4, 0x00000000u, 0x0u},
    {0x8006988Cu, func_8006988C, 0x00000000u, 0x0u},
    {0x80069B40u, func_80069B40, 0x00000000u, 0x0u},
    {0x80069E44u, func_80069E44, 0x00000000u, 0x0u},
    {0x80069F94u, func_80069F94, 0x00000000u, 0x0u},
    {0x8006A0E8u, func_8006A0E8, 0x00000000u, 0x0u},
    {0x8006A268u, func_8006A268, 0x00000000u, 0x0u},
    {0x8006A3F0u, func_8006A3F0, 0x00000000u, 0x0u},
    {0x8006A540u, func_8006A540, 0x00000000u, 0x0u},
    {0x8006A694u, func_8006A694, 0x00000000u, 0x0u},
    {0x8006A814u, func_8006A814, 0x00000000u, 0x0u},
    {0x8006A99Cu, func_8006A99C, 0x00000000u, 0x0u},
    {0x8006AAFCu, func_8006AAFC, 0x00000000u, 0x0u},
    {0x8006AC88u, func_8006AC88, 0x00000000u, 0x0u},
    {0x8006ADE8u, func_8006ADE8, 0x00000000u, 0x0u},
    {0x8006AF74u, func_8006AF74, 0x00000000u, 0x0u},
    {0x8006BCA4u, func_8006BCA4, 0x00000000u, 0x0u},
    {0x8006C120u, func_8006C120, 0x00000000u, 0x0u},
    {0x8006C2FCu, Triplet_SetComponents, 0x00000000u, 0x0u},
    {0x8006C30Cu, func_8006C30C, 0x00000000u, 0x0u},
    {0x8006C330u, func_8006C330, 0x00000000u, 0x0u},
    {0x8006C37Cu, Model_UpdateDiscEffect, 0x00000000u, 0x0u},
    {0x8006CD78u, func_8006CD78, 0x00000000u, 0x0u},
    {0x8006F1B4u, func_8006F1B4, 0x00000000u, 0x0u},
    {0x8007058Cu, AiScript_ReadByte, 0x00000000u, 0x0u},
    {0x800705ACu, AiScript_ReadShort, 0x00000000u, 0x0u},
    {0x800705D8u, AiScript_Init, 0x00000000u, 0x0u},
    {0x80070650u, AiScript_Run, 0x00000000u, 0x0u},
    {0x80070710u, Ai_GetHandSize, 0x00000000u, 0x0u},
    {0x80070738u, Ai_GetWinningCardRange, 0x00000000u, 0x0u},
    {0x800707C4u, Ai_GetCardRange, 0x00000000u, 0x0u},
    {0x80070870u, Ai_IsCardInSet, 0x00000000u, 0x0u},
    {0x800708C4u, Ai_IsTypeInSet, 0x00000000u, 0x0u},
    {0x80070920u, Ai_IsCardInSets, 0x00000000u, 0x0u},
    {0x80070988u, AiScript_Jump, 0x00000000u, 0x0u},
    {0x800709C0u, AiScript_JumpGreaterEqual, 0x00000000u, 0x0u},
    {0x80070A40u, AiScript_JumpGreater, 0x00000000u, 0x0u},
    {0x80070AC0u, AiScript_JumpEqual, 0x00000000u, 0x0u},
    {0x80070B3Cu, AiScript_JumpNotEqual, 0x00000000u, 0x0u},
    {0x80070BB8u, AiScript_JumpBetween, 0x00000000u, 0x0u},
    {0x80070C60u, AiScript_JumpRandom, 0x00000000u, 0x0u},
    {0x80070D00u, AiScript_Call, 0x00000000u, 0x0u},
    {0x80070DA8u, AiScript_Return, 0x00000000u, 0x0u},
    {0x80070E20u, AiScript_SetRandom, 0x00000000u, 0x0u},
    {0x80070EB4u, AiScript_Subtract, 0x00000000u, 0x0u},
    {0x80070F1Cu, AiScript_PlayFieldCard, 0x00000000u, 0x0u},
    {0x80070FF8u, AiScript_EndHand, 0x00000000u, 0x0u},
    {0x80071000u, AiScript_EndField, 0x00000000u, 0x0u},
    {0x80071008u, AiScript_CalcCardPower, 0x00000000u, 0x0u},
    {0x80071194u, AiScript_TestHighStat, 0x00000000u, 0x0u},
    {0x80071248u, AiScript_LoadCardType, 0x00000000u, 0x0u},
    {0x800712B4u, AiScript_LoadCardID, 0x00000000u, 0x0u},
    {0x80071320u, AiScript_SetFaceDown, 0x00000000u, 0x0u},
    {0x800713B8u, AiScript_LoadLifePoint, 0x00000000u, 0x0u},
    {0x80071424u, AiScript_LoadOpponentID, 0x00000000u, 0x0u},
    {0x80071460u, AiScript_LoadTerrain, 0x00000000u, 0x0u},
    {0x8007149Cu, AiScript_LoadDeckSize, 0x00000000u, 0x0u},
    {0x80071510u, AiScript_LoadSelectionRandom, 0x00000000u, 0x0u},
    {0x8007154Cu, AiScript_TestPinned, 0x00000000u, 0x0u},
    {0x800715C4u, AiScript_StartCombo, 0x00000000u, 0x0u},
    {0x8007164Cu, AiScript_LoadBestDifference, 0x00000000u, 0x0u},
    {0x80071688u, AiScript_LoadBestAttacker, 0x00000000u, 0x0u},
    {0x800716C4u, AiScript_LoadBestTarget, 0x00000000u, 0x0u},
    {0x80071700u, AiScript_FindStrongest, 0x00000000u, 0x0u},
    {0x80071924u, AiScript_FindWeakest, 0x00000000u, 0x0u},
    {0x80071B64u, AiScript_FindKiller, 0x00000000u, 0x0u},
    {0x80071CB0u, AiScript_FindDefenseStopper, 0x00000000u, 0x0u},
    {0x80071EB8u, AiScript_CountCards, 0x00000000u, 0x0u},
    {0x80071FC8u, AiScript_FindFirstCard, 0x00000000u, 0x0u},
    {0x8007214Cu, AiScript_FindCard, 0x00000000u, 0x0u},
    {0x800722CCu, AiScript_MatchType, 0x00000000u, 0x0u},
    {0x8007249Cu, AiScript_FindEquipTarget, 0x00000000u, 0x0u},
    {0x800725C4u, AiScript_CheckRitual, 0x00000000u, 0x0u},
    {0x80072640u, AiScript_FindFirstMonster, 0x00000000u, 0x0u},
    {0x800726F4u, AiScript_FindFirstType, 0x00000000u, 0x0u},
    {0x800727C0u, Ai_CompleteFusion, 0x00000000u, 0x0u},
    {0x80072A48u, AiScript_FindBestCombo, 0x00000000u, 0x0u},
    {0x80072DC0u, AiScript_EvaluateFusion, 0x00000000u, 0x0u},
    {0x80072F1Cu, AiScript_SkipHand, 0x00000000u, 0x0u},
    {0x80072F54u, AiScript_SkipField, 0x00000000u, 0x0u},
    {0x80072F8Cu, AiScript_PlayFaceUp, 0x00000000u, 0x0u},
    {0x80073050u, AiScript_SetPosition, 0x00000000u, 0x0u},
    {0x8007308Cu, AiScript_FindBestAttack, 0x00000000u, 0x0u},
    {0x80073220u, AiScript_PushComboCard, 0x00000000u, 0x0u},
    {0x800732A0u, AiScript_PushComboEmpty, 0x00000000u, 0x0u},
    {0x80073300u, AiScript_HandNop, 0x00000000u, 0x0u},
    {0x80073308u, AiScript_FieldNop, 0x00000000u, 0x0u},
    {0x80073310u, AiScript_AddCard, 0x00000000u, 0x0u},
    {0x80073380u, AiScript_ClearCards, 0x00000000u, 0x0u},
    {0x800733A8u, AiScript_AddType, 0x00000000u, 0x0u},
    {0x80073420u, AiScript_ClearTypes, 0x00000000u, 0x0u},
    {0x80073448u, AiScript_SetSelectionRandom, 0x00000000u, 0x0u},
    {0x80073458u, AiScript_ClearSelectionRandom, 0x00000000u, 0x0u},
    {0x80073464u, func_80073464, 0x00000000u, 0x0u},
    {0x80073474u, func_80073474, 0x00000000u, 0x0u},
    {0x80073480u, AiScript_MoveCard, 0x00000000u, 0x0u},
    {0x800734DCu, AiScript_LoadOpponentData, 0x00000000u, 0x0u},
    {0x800735A0u, AiScript_Store, 0x00000000u, 0x0u},
    {0x800735DCu, AiScript_SetRegister, 0x00000000u, 0x0u},
    {0x80073624u, AiScript_Add, 0x00000000u, 0x0u},
    {0x8007368Cu, AiScript_LoadGuardianStarChoice, 0x00000000u, 0x0u},
    {0x800736C4u, AiScript_Print, 0x00000000u, 0x0u},
    {0x80073704u, PCopen, 0x00000000u, 0x0u},
    {0x80073724u, PCclose, 0x00000000u, 0x0u},
    {0x80073734u, PClseek, 0x00000000u, 0x0u},
    {0x80073758u, PCread, 0x00000000u, 0x0u},
    {0x80073840u, _bu_init, 0x00000000u, 0x0u},
    {0x80073850u, SetMem, 0x00000000u, 0x0u},
    {0x80073860u, OpenEvent, 0x00000000u, 0x0u},
    {0x80073870u, CloseEvent, 0x00000000u, 0x0u},
    {0x80073880u, TestEvent, 0x00000000u, 0x0u},
    {0x80073890u, EnableEvent, 0x00000000u, 0x0u},
    {0x800738A0u, DisableEvent, 0x00000000u, 0x0u},
    {0x800738B0u, EnterCriticalSection, 0x00000000u, 0x0u},
    {0x800738C0u, ExitCriticalSection, 0x00000000u, 0x0u},
    {0x80073920u, nextfile, 0x00000000u, 0x0u},
    {0x80073930u, Krom2RawAdd, 0x00000000u, 0x0u},
    {0x80073940u, ChangeClearPAD, 0x00000000u, 0x0u},
    {0x80073950u, SetRCnt, 0x00000000u, 0x0u},
    {0x800739ECu, GetRCnt, 0x00000000u, 0x0u},
    {0x80073A24u, StartRCnt, 0x00000000u, 0x0u},
    {0x80073A54u, StopRCnt, 0x00000000u, 0x0u},
    {0x80073AC0u, firstfile, 0x00000000u, 0x0u},
    {0x80073E1Cu, InitPAD, 0x00000000u, 0x0u},
    {0x80073EACu, StartPAD, 0x00000000u, 0x0u},
    {0x80074170u, VSync, 0x00000000u, 0x0u},
    {0x80074390u, ResetCallback, 0x00000000u, 0x0u},
    {0x80074420u, VSyncCallback, 0x00000000u, 0x0u},
    {0x80074484u, StopCallback, 0x00000000u, 0x0u},
    {0x80074E60u, SpuInit, 0x00000000u, 0x0u},
    {0x80075B60u, SpuQuit, 0x00000000u, 0x0u},
    {0x80075BE0u, SpuSetReverb, 0x00000000u, 0x0u},
    {0x80075DC0u, SpuGetReverb, 0x00000000u, 0x0u},
    {0x80075DE0u, SpuSetReverbModeParam, 0x00000000u, 0x0u},
    {0x80076790u, SpuReserveReverbWorkArea, 0x00000000u, 0x0u},
    {0x800767E0u, SpuIsReverbWorkAreaReserved, 0x00000000u, 0x0u},
    {0x80076820u, SpuSetReverbVoice, 0x00000000u, 0x0u},
    {0x80076B10u, SpuGetReverbVoice, 0x00000000u, 0x0u},
    {0x80076D20u, SpuReadDecodedData, 0x00000000u, 0x0u},
    {0x80076D90u, SpuSetIRQ, 0x00000000u, 0x0u},
    {0x80076ED0u, SpuSetKey, 0x00000000u, 0x0u},
    {0x80077090u, SpuGetKeyStatus, 0x00000000u, 0x0u},
    {0x80077120u, SpuSetKeyOnWithAttr, 0x00000000u, 0x0u},
    {0x80077150u, SpuWrite, 0x00000000u, 0x0u},
    {0x800771B0u, SpuSetTransferStartAddr, 0x00000000u, 0x0u},
    {0x80077210u, SpuSetTransferMode, 0x00000000u, 0x0u},
    {0x80077240u, SpuIsTransferCompleted, 0x00000000u, 0x0u},
    {0x800773C4u, SpuGetAllKeysStatus, 0x00000000u, 0x0u},
    {0x80077450u, SpuSetVoiceAttr, 0x00000000u, 0x0u},
    {0x80077C50u, SpuGetVoiceEnvelope, 0x00000000u, 0x0u},
    {0x80077C70u, SpuSetCommonAttr, 0x00000000u, 0x0u},
    {0x80077FF0u, SpuSetReverbModeType, 0x00000000u, 0x0u},
    {0x800781C0u, StSetRing, 0x00000000u, 0x0u},
    {0x800781F0u, CdPosToInt, 0x00000000u, 0x0u},
    {0x80078270u, StClearRing, 0x00000000u, 0x0u},
    {0x800782D0u, StUnSetRing, 0x00000000u, 0x0u},
    {0x800783DCu, StGetBackloc, 0x00000000u, 0x0u},
    {0x80078440u, StSetStream, 0x00000000u, 0x0u},
    {0x800784D0u, StFreeRing, 0x00000000u, 0x0u},
    {0x800785C0u, StGetNext, 0x00000000u, 0x0u},
    {0x800786A0u, StCdInterrupt, 0x00000000u, 0x0u},
    {0x8007AFA4u, DsInit, 0x00000000u, 0x0u},
    {0x8007B1F4u, DsCommand, 0x00000000u, 0x0u},
    {0x8007B468u, DsPacket, 0x00000000u, 0x0u},
    {0x8007CDC0u, CdMix, 0x00000000u, 0x0u},
    {0x8007D2F0u, DsRead2, 0x00000000u, 0x0u},
    {0x8007D3F0u, DsSearchFile, 0x00000000u, 0x0u},
    {0x8007DD50u, DsStartReadySystem, 0x00000000u, 0x0u},
    {0x8007DDD4u, DsEndReadySystem, 0x00000000u, 0x0u},
    {0x8007DE38u, DsReadySystemMode, 0x00000000u, 0x0u},
    {0x8007E350u, CdFlush, 0x00000000u, 0x0u},
    {0x8007E3D0u, CdGetSector, 0x00000000u, 0x0u},
    {0x8007E600u, CdIntToPos_8007E600, 0x00000000u, 0x0u},
    {0x8007E710u, CdPosToInt_8007E710, 0x00000000u, 0x0u},
    {0x8007E7F0u, CdControlB, 0x00000000u, 0x0u},
    {0x8007E860u, CdReadyCallback, 0x00000000u, 0x0u},
    {0x8007E8D0u, SetDumpFnt, 0x00000000u, 0x0u},
    {0x8007E910u, FntLoad, 0x00000000u, 0x0u},
    {0x8007E9B0u, FntOpen, 0x00000000u, 0x0u},
    {0x8007EC68u, FntFlush, 0x00000000u, 0x0u},
    {0x8007EF84u, FntPrint, 0x00000000u, 0x0u},
    {0x8007F350u, ResetGraph, 0x00000000u, 0x0u},
    {0x8007F634u, SetDispMask, 0x00000000u, 0x0u},
    {0x8007F6CCu, DrawSync, 0x00000000u, 0x0u},
    {0x8007F850u, ClearImage, 0x00000000u, 0x0u},
    {0x8007F978u, LoadImage, 0x00000000u, 0x0u},
    {0x8007F9D8u, StoreImage, 0x00000000u, 0x0u},
    {0x8007FA38u, MoveImage, 0x00000000u, 0x0u},
    {0x8007FCC0u, DrawOTag, 0x00000000u, 0x0u},
    {0x8007FD30u, PutDrawEnv, 0x00000000u, 0x0u},
    {0x8007FEC8u, GetDrawEnv, 0x00000000u, 0x0u},
    {0x8007FEFCu, PutDispEnv, 0x00000000u, 0x0u},
    {0x800803F4u, GetDispEnv, 0x00000000u, 0x0u},
    {0x80081DE8u, LoadImage2, 0x00000000u, 0x0u},
    {0x80081ED4u, StoreImage2, 0x00000000u, 0x0u},
    {0x80081FC0u, MoveImage2, 0x00000000u, 0x0u},
    {0x80082274u, GetVideoMode, 0x00000000u, 0x0u},
    {0x80082324u, IsIdleGPU, 0x00000000u, 0x0u},
    {0x80082780u, GetTPage, 0x00000000u, 0x0u},
    {0x800827C0u, GetClut, 0x00000000u, 0x0u},
    {0x80082840u, SetSemiTrans, 0x00000000u, 0x0u},
    {0x80082870u, SetShadeTex, 0x00000000u, 0x0u},
    {0x800828A0u, SetPolyF3, 0x00000000u, 0x0u},
    {0x800828C0u, SetPolyFT3, 0x00000000u, 0x0u},
    {0x800828E0u, SetPolyG3, 0x00000000u, 0x0u},
    {0x80082900u, SetPolyGT3, 0x00000000u, 0x0u},
    {0x80082920u, SetPolyF4, 0x00000000u, 0x0u},
    {0x80082940u, SetPolyFT4, 0x00000000u, 0x0u},
    {0x80082960u, SetPolyG4, 0x00000000u, 0x0u},
    {0x80082980u, SetPolyGT4, 0x00000000u, 0x0u},
    {0x80082C10u, Krom2RawAdd2, 0x00000000u, 0x0u},
    {0x80083FB0u, GsSortLine, 0x00000000u, 0x0u},
    {0x80084130u, GsSortGLine, 0x00000000u, 0x0u},
    {0x80084240u, GsSortBoxFill, 0x00000000u, 0x0u},
    {0x80084320u, GsSortPoly, 0x00000000u, 0x0u},
    {0x800844F0u, GsSortSprite, 0x00000000u, 0x0u},
    {0x800849F0u, GsSortFastSprite, 0x00000000u, 0x0u},
    {0x80084B70u, GsSortFlipSprite, 0x00000000u, 0x0u},
    {0x80084DD0u, GsInitGraph, 0x00000000u, 0x0u},
    {0x80084F60u, GsInitGraph2, 0x00000000u, 0x0u},
    {0x80085320u, GsGetActiveBuff, 0x00000000u, 0x0u},
    {0x800854C0u, GsInitVcount, 0x00000000u, 0x0u},
    {0x80085500u, GsSwapDispBuff, 0x00000000u, 0x0u},
    {0x800855B0u, GsSetOrign, 0x00000000u, 0x0u},
    {0x800855D0u, GsSetLsMatrix, 0x00000000u, 0x0u},
    {0x80085600u, GsSetLightMatrix, 0x00000000u, 0x0u},
    {0x800856A0u, GsDefDispBuff, 0x00000000u, 0x0u},
    {0x80085740u, GsInit3D, 0x00000000u, 0x0u},
    {0x800857C0u, GsSetProjection, 0x00000000u, 0x0u},
    {0x800857E0u, GsSetFlatLight, 0x00000000u, 0x0u},
    {0x80085D50u, GsSetAmbient, 0x00000000u, 0x0u},
    {0x80085D80u, GsDrawOt, 0x00000000u, 0x0u},
    {0x80085DB0u, GsClearOt, 0x00000000u, 0x0u},
    {0x80085E10u, GsSortOt, 0x00000000u, 0x0u},
    {0x80086100u, GsGetTimInfo, 0x00000000u, 0x0u},
    {0x800862C0u, GsSetWorkBase, 0x00000000u, 0x0u},
    {0x800862D0u, GsGetLs, 0x00000000u, 0x0u},
    {0x800865A0u, GsMulCoord2, 0x00000000u, 0x0u},
    {0x80086620u, GsMulCoord3, 0x00000000u, 0x0u},
    {0x800866A0u, rsin, 0x00000000u, 0x0u},
    {0x80086770u, rcos, 0x00000000u, 0x0u},
    {0x80086810u, SetFogNearFar, 0x00000000u, 0x0u},
    {0x80086CF0u, catan, 0x00000000u, 0x0u},
    {0x80086DC8u, InitGeom, 0x00000000u, 0x0u},
    {0x80086E50u, SquareRoot0, 0x00000000u, 0x0u},
    {0x80086EE0u, gteMIMefunc, 0x00000000u, 0x0u},
    {0x80086F60u, MulMatrix0, 0x00000000u, 0x0u},
    {0x80087070u, ApplyMatrixLV, 0x00000000u, 0x0u},
    {0x800871D0u, PushMatrix, 0x00000000u, 0x0u},
    {0x80087274u, PopMatrix, 0x00000000u, 0x0u},
    {0x80087320u, ReadRotMatrix, 0x00000000u, 0x0u},
    {0x80087370u, MulMatrix, 0x00000000u, 0x0u},
    {0x80087480u, MulMatrix2, 0x00000000u, 0x0u},
    {0x80087590u, ApplyMatrix, 0x00000000u, 0x0u},
    {0x800875E0u, ApplyMatrixSV, 0x00000000u, 0x0u},
    {0x80087640u, TransMatrix, 0x00000000u, 0x0u},
    {0x80087670u, ScaleMatrix, 0x00000000u, 0x0u},
    {0x800877B0u, SetRotMatrix, 0x00000000u, 0x0u},
    {0x800877E0u, SetLightMatrix, 0x00000000u, 0x0u},
    {0x80087810u, SetColorMatrix, 0x00000000u, 0x0u},
    {0x80087840u, SetTransMatrix, 0x00000000u, 0x0u},
    {0x80087860u, ReadGeomScreen, 0x00000000u, 0x0u},
    {0x80087870u, SetBackColor, 0x00000000u, 0x0u},
    {0x80087890u, SetFarColor, 0x00000000u, 0x0u},
    {0x800878B0u, SetGeomOffset, 0x00000000u, 0x0u},
    {0x800878D0u, SetGeomScreen, 0x00000000u, 0x0u},
    {0x800878E0u, RotTransPers, 0x00000000u, 0x0u},
    {0x80087910u, RotTransPers3, 0x00000000u, 0x0u},
    {0x80087970u, RotTrans, 0x00000000u, 0x0u},
    {0x800879A0u, NormalClip, 0x00000000u, 0x0u},
    {0x800879D0u, RotTransPers4, 0x00000000u, 0x0u},
    {0x80087A50u, RotAverage3, 0x00000000u, 0x0u},
    {0x80087AB0u, RotAverage4, 0x00000000u, 0x0u},
    {0x80087B30u, RotAverageNclip3, 0x00000000u, 0x0u},
    {0x80087BC0u, RotAverageNclip4, 0x00000000u, 0x0u},
    {0x80087C70u, RotColorDpq, 0x00000000u, 0x0u},
    {0x80087CC0u, RotTransPersN, 0x00000000u, 0x0u},
    {0x80087D30u, RotMatrix, 0x00000000u, 0x0u},
    {0x80087FC0u, RotMatrixYXZ, 0x00000000u, 0x0u},
    {0x80088250u, RotMatrixZYX, 0x00000000u, 0x0u},
    {0x800884E0u, RotMatrixX, 0x00000000u, 0x0u},
    {0x80088680u, RotMatrixY, 0x00000000u, 0x0u},
    {0x80088820u, RotMatrixZ, 0x00000000u, 0x0u},
    {0x800889C0u, RotMatrixZXY, 0x00000000u, 0x0u},
    {0x80088C50u, RotMatrixZYX_gte, 0x00000000u, 0x0u},
    {0x80088E50u, RotMatrix_gte, 0x00000000u, 0x0u},
    {0x80089060u, RotMatrixYXZ_gte, 0x00000000u, 0x0u},
    {0x80089260u, DivideFT4, 0x00000000u, 0x0u},
    {0x800899A0u, ratan2, 0x00000000u, 0x0u},
    {0x80089C20u, NormalColorCol, 0x00000000u, 0x0u},
    {0x80089C40u, Square0, 0x00000000u, 0x0u},
    {0x80089C70u, AverageZ3, 0x00000000u, 0x0u},
    {0x80089C90u, AverageZ4, 0x00000000u, 0x0u},
    {0x80089CC0u, RotTransSV, 0x00000000u, 0x0u},
    {0x80089CF0u, RotAverageNclip3_nom, 0x00000000u, 0x0u},
    {0x80089D30u, GsScanAnim, 0x00000000u, 0x0u},
    {0x80089DD8u, GsLinkAnim, 0x00000000u, 0x0u},
    {0x80089E20u, GsU_00000000, 0x00000000u, 0x0u},
    {0x80089E40u, GsU_02000000, 0x00000000u, 0x0u},
    {0x80089ED0u, GsU_02000001, 0x00000000u, 0x0u},
    {0x80089F80u, GsScanUnit, 0x00000000u, 0x0u},
    {0x8008A138u, GsGetHeadpUnit, 0x00000000u, 0x0u},
    {0x8008A150u, GsSortUnit, 0x00000000u, 0x0u},
    {0x8008A280u, GsMapUnit, 0x00000000u, 0x0u},
    {0x8008A420u, GsMapCoordUnit, 0x00000000u, 0x0u},
    {0x8008A4A0u, GsGetLwUnit, 0x00000000u, 0x0u},
    {0x8008A760u, GsGetLsUnit, 0x00000000u, 0x0u},
    {0x8008AA30u, GsGetLwsUnit, 0x00000000u, 0x0u},
    {0x8008AD50u, GsSetRefView2, 0x00000000u, 0x0u},
    {0x8008B2F0u, TransposeMatrix, 0x00000000u, 0x0u},
    {0x8008B330u, _card_info, 0x00000000u, 0x0u},
    {0x8008B340u, _card_load, 0x00000000u, 0x0u},
    {0x8008B350u, _card_write, 0x00000000u, 0x0u},
    {0x8008B360u, _card_read, 0x00000000u, 0x0u},
    {0x8008B370u, _new_card, 0x00000000u, 0x0u},
    {0x8008B380u, _card_status, 0x00000000u, 0x0u},
    {0x8008B390u, _card_wait, 0x00000000u, 0x0u},
    {0x8008B3A0u, _card_clear, 0x00000000u, 0x0u},
    {0x8008B3E0u, InitCARD, 0x00000000u, 0x0u},
    {0x8008B470u, StartCARD, 0x00000000u, 0x0u},
    {0x8008B7B0u, MemCardInit, 0x00000000u, 0x0u},
    {0x8008B7E0u, MemCardEnd, 0x00000000u, 0x0u},
    {0x8008B85Cu, MemCardStart, 0x00000000u, 0x0u},
    {0x8008B8CCu, MemCardStop, 0x00000000u, 0x0u},
    {0x8008B90Cu, MemCardExist, 0x00000000u, 0x0u},
    {0x8008BC90u, MemCardAccept, 0x00000000u, 0x0u},
    {0x8008C638u, MemCardReadFile, 0x00000000u, 0x0u},
    {0x8008C858u, MemCardWriteFile, 0x00000000u, 0x0u},
    {0x8008CA78u, MemCardGetDirentry, 0x00000000u, 0x0u},
    {0x8008CCE8u, MemCardSync, 0x00000000u, 0x0u},
    {0x8008CE04u, MemCardCreateFile, 0x00000000u, 0x0u},
    {0x8008CF00u, MemCardFormat, 0x00000000u, 0x0u},
    {0x8008E360u, bzero, 0x00000000u, 0x0u},
    {0x8008FBE0u, DecDCTReset, 0x00000000u, 0x0u},
    {0x8008FD38u, DecDCTin, 0x00000000u, 0x0u},
    {0x8008FDB4u, DecDCTout, 0x00000000u, 0x0u},
    {0x8008FE7Cu, DecDCToutCallback, 0x00000000u, 0x0u},
    {0x800902A0u, DecDCTvlc2, 0x00000000u, 0x0u},
    {0x800905F0u, DecDCTvlcBuild, 0x00000000u, 0x0u},
    {0x8013A004u, Memories_ModelPrimaryControlA, 0x00000000u, 0x0u},
    {0x8013B004u, Memories_ModelVariantControlA, 0x00000000u, 0x0u},
    {0x801462B0u, Memories_DuelEffectControl, 0x00000000u, 0x0u},
    {0x80168004u, CampaignMap_ClearLocationObjects, 0x80168000u, 0x14u},
    {0x80168004u, FreeDuel_UpdateScrollbar, 0x80168000u, 0x13u},
    {0x80168050u, CampaignMap_RebuildLocationObjects, 0x80168000u, 0x14u},
    {0x80168090u, FreeDuel_PlaceCursor, 0x80168000u, 0x13u},
    {0x801680B4u, func_801680B4, 0x80168000u, 0x15u},
    {0x80168138u, NameEntry_BuildKeyboardTextBox, 0x80168000u, 0x15u},
    {0x8016818Cu, CampaignMap_CreateLocationLabel, 0x80168000u, 0x14u},
    {0x801681A0u, NameEntry_DrawSelectionFrame, 0x80168000u, 0x15u},
    {0x801681B4u, FreeDuel_SpawnSparkle, 0x80168000u, 0x13u},
    {0x801681E8u, CampaignMap_SetCameraFromLocation, 0x80168000u, 0x14u},
    {0x8016824Cu, FreeDuel_Init, 0x80168000u, 0x13u},
    {0x80168258u, CampaignMap_UpdateView, 0x80168000u, 0x14u},
    {0x80168310u, CampaignMap_ResetCamera, 0x80168000u, 0x14u},
    {0x80168388u, CampaignMap_MoveCameraDpad, 0x80168000u, 0x14u},
    {0x801683ECu, NameEntry_Init, 0x80168000u, 0x15u},
    {0x80168588u, CampaignMap_CreateLocationMarker, 0x80168000u, 0x14u},
    {0x8016866Cu, CampaignMap_SetLocation, 0x80168000u, 0x14u},
    {0x8016868Cu, TextBox_GetGlyphAt, 0x80168000u, 0x15u},
    {0x80168708u, NameEntry_UpdateGlyphPulse, 0x80168000u, 0x15u},
    {0x80168808u, NameEntry_UpdateGlyphFragment, 0x80168000u, 0x15u},
    {0x801688ACu, NameEntry_UpdateGlyphShatter, 0x80168000u, 0x15u},
    {0x801688BCu, CampaignMap_StartCameraTween, 0x80168000u, 0x14u},
    {0x8016899Cu, FreeDuel_GetSparkleSlot, 0x80168000u, 0x13u},
    {0x801689B4u, NameEntry_UpdateCaretTween, 0x80168000u, 0x15u},
    {0x801689D4u, FreeDuel_UpdateSparkle, 0x80168000u, 0x13u},
    {0x80168A9Cu, FreeDuel_UpdateCursorTween, 0x80168000u, 0x13u},
    {0x80168AA8u, CampaignMap_UpdateLocationTransition, 0x80168000u, 0x14u},
    {0x80168AB4u, NameEntry_UpdateGlyphTransfer, 0x80168000u, 0x15u},
    {0x80168C7Cu, FreeDuel_UpdateScreen, 0x80168000u, 0x13u},
    {0x80168CDCu, NameEntry_SpawnGlyphSprite, 0x80168000u, 0x15u},
    {0x80168E0Cu, CampaignMap_PickExit, 0x80168000u, 0x14u},
    {0x80168FB4u, FreeDuel_Entry, 0x80168000u, 0x13u},
    {0x80168FCCu, CampaignMap_UpdateLocation, 0x80168000u, 0x14u},
    {0x8016909Cu, NameEntry_AdjustLength, 0x80168000u, 0x15u},
    {0x8016913Cu, NameEntry_UpdateKeyboard, 0x80168000u, 0x15u},
    {0x80169734u, NameEntry_UpdateDialog, 0x80168000u, 0x15u},
    {0x801697D0u, CampaignMap_PickAlternateExit, 0x80168000u, 0x14u},
    {0x80169A9Cu, CampaignMap_UpdateAlternateLocation, 0x80168000u, 0x14u},
    {0x80169C08u, NameEntry_PollCompletion, 0x80168000u, 0x15u},
    {0x80169C30u, Password_RefreshDigitDisplay, 0x80168000u, 0x15u},
    {0x80169D10u, Password_RefreshStarchipDisplay, 0x80168000u, 0x15u},
    {0x80169D84u, Password_CreateMessageBox, 0x80168000u, 0x15u},
    {0x80169E20u, Password_UpdateDigitCursor, 0x80168000u, 0x15u},
    {0x80169F38u, Password_UpdateDigitCursorDecoration, 0x80168000u, 0x15u},
    {0x8016A00Cu, Password_SetDigitCursorTarget, 0x80168000u, 0x15u},
    {0x8016A02Cu, Password_RecreateCardPreview, 0x80168000u, 0x15u},
    {0x8016A080u, Password_InitShopScreen, 0x80168000u, 0x15u},
    {0x8016A304u, Password_LookupCardID, 0x80168000u, 0x15u},
    {0x8016A37Cu, Password_UpdateShopScreen, 0x80168000u, 0x15u},
    {0x8016A930u, NameEntry_BuildStarterDeck, 0x80168000u, 0x15u},
    {0x8016AA6Cu, NameEntry_Main, 0x80168000u, 0x15u},
    {0x8017A004u, Memories_ModelPrimaryControlB, 0x00000000u, 0x0u},
    {0x8017B004u, Memories_ModelVariantControlB, 0x00000000u, 0x0u},
    {0x8018001Cu, MainMenu_InitFrontendMenu, 0x00000000u, 0x0u},
    {0x80180390u, MainMenu_UpdateFrontendMenu, 0x00000000u, 0x0u},
    {0x801807B0u, Memories_CreditsInit, 0x00000000u, 0x0u},
    {0x80180A24u, Memories_CreditsUpdate, 0x00000000u, 0x0u},
    {0x80180B4Cu, MainMenu_DrawFrontendBackground, 0x00000000u, 0x0u},
    {0x80180D2Cu, MainMenu_StartFrontendEntryTransition, 0x00000000u, 0x0u},
    {0x80180DD0u, MainMenu_DestroyFrontendMenu, 0x00000000u, 0x0u},
    {0x80180E6Cu, MainMenu_SpawnFrontendEntryAfterimage, 0x00000000u, 0x0u},
    {0x80180F50u, MainMenu_UpdateFrontendEntryAfterimage, 0x00000000u, 0x0u},
    {0x80180FD8u, MainMenu_StartValueSetup, 0x00000000u, 0x0u},
    {0x801812B4u, MainMenu_UpdateValueSetup, 0x00000000u, 0x0u},
    {0x80181728u, MainMenu_DrawValueSetup, 0x00000000u, 0x0u},
    {0x80181C4Cu, Memories_CreditsLines, 0x00000000u, 0x0u},
    {0x80181CB8u, MainMenu_UpdateValueWidgetTween, 0x00000000u, 0x0u},
    {0x80181E30u, MainMenu_FinishValueSetup, 0x00000000u, 0x0u},
    {0x80181EECu, MainMenu_CountDecimalDigits, 0x00000000u, 0x0u},
    {0x80181F20u, MainMenu_StartValueWidgetTween, 0x00000000u, 0x0u},
    {0x80181F68u, MainMenu_InitTradeScreen, 0x00000000u, 0x0u},
    {0x801821DCu, MainMenu_UpdateTradeScreen, 0x00000000u, 0x0u},
    {0x8018338Cu, MainMenu_RefreshTradeInventory, 0x00000000u, 0x0u},
    {0x80183514u, MainMenu_CompareCardsByMaxStat, 0x00000000u, 0x0u},
    {0x801836F4u, MainMenu_CompareCardsByAttack, 0x00000000u, 0x0u},
    {0x80183884u, MainMenu_CompareCardsByDefense, 0x00000000u, 0x0u},
    {0x80183A14u, MainMenu_CompareCardsByType, 0x00000000u, 0x0u},
    {0x80183B2Cu, MainMenu_DrawTradeOffersAndHighlights, 0x00000000u, 0x0u},
    {0x80183E8Cu, MainMenu_DrawThreeDigitNumber, 0x00000000u, 0x0u},
    {0x80183FE4u, MainMenu_ReleaseTradeDisplayHandles, 0x00000000u, 0x0u},
    {0x80184030u, MainMenu_ApplyTradeOfferInventoryDelta, 0x00000000u, 0x0u},
    {0x801840F8u, MainMenu_AdjustTradeCardCount, 0x00000000u, 0x0u},
    {0x8018416Cu, MainMenu_CompareCardsByName, 0x00000000u, 0x0u},
    {0x80184254u, MainMenu_CompareCardsByCount, 0x00000000u, 0x0u},
    {0x80184344u, MainMenu_DrawCardTypeIcon, 0x00000000u, 0x0u},
    {0x80184454u, MainMenu_DrawTradeColumnOverlay, 0x00000000u, 0x0u},
    {0x801844D8u, MainMenu_RebuildTradeInventoryRows, 0x00000000u, 0x0u},
};
const unsigned Memories_FunctionMapCount = 1523;
extern char __start_ovl_password_data[], __stop_ovl_password_data[];
extern char __start_ovl_password_bss[], __stop_ovl_password_bss[];
extern char __start_ovl_overworld_data[], __stop_ovl_overworld_data[];
extern char __start_ovl_overworld_bss[], __stop_ovl_overworld_bss[];
extern char __start_ovl_free_duel_data[], __stop_ovl_free_duel_data[];
extern char __start_ovl_free_duel_bss[], __stop_ovl_free_duel_bss[];
const MemoriesModule Memories_Modules[] = {
    {"password", 0x80168000u, 0x15u, __start_ovl_password_data, __stop_ovl_password_data, __start_ovl_password_bss, __stop_ovl_password_bss},
    {"overworld", 0x80168000u, 0x14u, __start_ovl_overworld_data, __stop_ovl_overworld_data, __start_ovl_overworld_bss, __stop_ovl_overworld_bss},
    {"free_duel", 0x80168000u, 0x13u, __start_ovl_free_duel_data, __stop_ovl_free_duel_data, __start_ovl_free_duel_bss, __stop_ovl_free_duel_bss},
};
const unsigned Memories_ModuleCount = 3;
