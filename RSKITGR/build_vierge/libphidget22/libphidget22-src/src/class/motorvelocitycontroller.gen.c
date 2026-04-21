/* Generated: Mon Mar 04 2024 17:00:45 GMT-0700 (Mountain Standard Time) */

static void CCONV PhidgetMotorVelocityController_errorHandler(PhidgetChannelHandle ch,
  Phidget_ErrorEventCode code);
static void CCONV PhidgetMotorVelocityController_free(PhidgetChannelHandle *ch);
static PhidgetReturnCode CCONV PhidgetMotorVelocityController_bridgeInput(PhidgetChannelHandle phid,
  BridgePacket *bp);
static PhidgetReturnCode CCONV PhidgetMotorVelocityController_setStatus(PhidgetChannelHandle phid,
  BridgePacket *bp);
static PhidgetReturnCode CCONV PhidgetMotorVelocityController_getStatus(PhidgetChannelHandle phid,
  BridgePacket **bp);
static PhidgetReturnCode CCONV PhidgetMotorVelocityController_initAfterOpen(PhidgetChannelHandle phid);
static PhidgetReturnCode CCONV PhidgetMotorVelocityController_setDefaults(PhidgetChannelHandle phid);
static void CCONV PhidgetMotorVelocityController_fireInitialEvents(PhidgetChannelHandle phid);
static int CCONV PhidgetMotorVelocityController_hasInitialState(PhidgetChannelHandle phid);

struct _PhidgetMotorVelocityController {
	struct _PhidgetChannel phid;
	double acceleration;
	double minAcceleration;
	double maxAcceleration;
	double activeCurrentLimit;
	double minBrakingStrength;
	double maxBrakingStrength;
	double currentLimit;
	double minCurrentLimit;
	double maxCurrentLimit;
	double dataInterval;
	uint32_t minDataInterval;
	uint32_t maxDataInterval;
	double minDataRate;
	double maxDataRate;
	double deadBand;
	double dutyCycle;
	int engaged;
	double expectedVelocity;
	int enableExpectedVelocity;
	double failsafeBrakingStrength;
	double failsafeCurrentLimit;
	uint32_t minFailsafeTime;
	uint32_t maxFailsafeTime;
	double inductance;
	double minInductance;
	double maxInductance;
	double kd;
	double ki;
	double kp;
	Phidget_PositionType positionType;
	double rescaleFactor;
	double stallVelocity;
	double minStallVelocity;
	double maxStallVelocity;
	double surgeCurrentLimit;
	double minSurgeCurrentLimit;
	double maxSurgeCurrentLimit;
	double targetVelocity;
	double minTargetVelocity;
	double maxTargetVelocity;
	double velocity;
	PhidgetMotorVelocityController_OnDutyCycleUpdateCallback DutyCycleUpdate;
	void *DutyCycleUpdateCtx;
	PhidgetMotorVelocityController_OnExpectedVelocityChangeCallback ExpectedVelocityChange;
	void *ExpectedVelocityChangeCtx;
	PhidgetMotorVelocityController_OnVelocityChangeCallback VelocityChange;
	void *VelocityChangeCtx;
};

static PhidgetReturnCode CCONV
_setStatus(PhidgetChannelHandle phid, BridgePacket *bp) {
	PhidgetMotorVelocityControllerHandle ch;
	int nsversion;

	ch = (PhidgetMotorVelocityControllerHandle)phid;

	nsversion = getBridgePacketUInt32ByName(bp, "_class_version_");
	if (nsversion != 1) {
		loginfo("%"PRIphid": server/client class version mismatch: %d != 1 - functionality may be limited.", phid, nsversion);
	}

	if (hasBridgePacketByName(bp, "acceleration"))
		ch->acceleration = getBridgePacketDoubleByName(bp, "acceleration");
	if (hasBridgePacketByName(bp, "minAcceleration"))
		ch->minAcceleration = getBridgePacketDoubleByName(bp, "minAcceleration");
	if (hasBridgePacketByName(bp, "maxAcceleration"))
		ch->maxAcceleration = getBridgePacketDoubleByName(bp, "maxAcceleration");
	if (hasBridgePacketByName(bp, "activeCurrentLimit"))
		ch->activeCurrentLimit = getBridgePacketDoubleByName(bp, "activeCurrentLimit");
	if (hasBridgePacketByName(bp, "minBrakingStrength"))
		ch->minBrakingStrength = getBridgePacketDoubleByName(bp, "minBrakingStrength");
	if (hasBridgePacketByName(bp, "maxBrakingStrength"))
		ch->maxBrakingStrength = getBridgePacketDoubleByName(bp, "maxBrakingStrength");
	if (hasBridgePacketByName(bp, "currentLimit"))
		ch->currentLimit = getBridgePacketDoubleByName(bp, "currentLimit");
	if (hasBridgePacketByName(bp, "minCurrentLimit"))
		ch->minCurrentLimit = getBridgePacketDoubleByName(bp, "minCurrentLimit");
	if (hasBridgePacketByName(bp, "maxCurrentLimit"))
		ch->maxCurrentLimit = getBridgePacketDoubleByName(bp, "maxCurrentLimit");
	if (hasBridgePacketByName(bp, "minDataInterval"))
		ch->minDataInterval = getBridgePacketUInt32ByName(bp, "minDataInterval");
	if (hasBridgePacketByName(bp, "maxDataInterval"))
		ch->maxDataInterval = getBridgePacketUInt32ByName(bp, "maxDataInterval");
	if (hasBridgePacketByName(bp, "dataIntervalDbl"))
		ch->dataInterval = getBridgePacketDoubleByName(bp, "dataIntervalDbl");
	else if(hasBridgePacketByName(bp, "dataInterval"))
		ch->dataInterval = (double)getBridgePacketUInt32ByName(bp, "dataInterval");
	if (hasBridgePacketByName(bp, "minDataRate"))
		ch->minDataRate = getBridgePacketDoubleByName(bp, "minDataRate");
	else if(hasBridgePacketByName(bp, "maxDataInterval"))
		ch->minDataRate = (double)(1000.0 / getBridgePacketUInt32ByName(bp, "maxDataInterval"));
	if (hasBridgePacketByName(bp, "maxDataRate"))
		ch->maxDataRate = getBridgePacketDoubleByName(bp, "maxDataRate");
	else if(hasBridgePacketByName(bp, "minDataInterval"))
		ch->maxDataRate = (double)(1000.0 / getBridgePacketUInt32ByName(bp, "minDataInterval"));
	if (hasBridgePacketByName(bp, "deadBand"))
		ch->deadBand = getBridgePacketDoubleByName(bp, "deadBand");
	if (hasBridgePacketByName(bp, "dutyCycle"))
		ch->dutyCycle = getBridgePacketDoubleByName(bp, "dutyCycle");
	if (hasBridgePacketByName(bp, "engaged"))
		ch->engaged = getBridgePacketInt32ByName(bp, "engaged");
	if (hasBridgePacketByName(bp, "expectedVelocity"))
		ch->expectedVelocity = getBridgePacketDoubleByName(bp, "expectedVelocity");
	if (hasBridgePacketByName(bp, "enableExpectedVelocity"))
		ch->enableExpectedVelocity = getBridgePacketInt32ByName(bp, "enableExpectedVelocity");
	if (hasBridgePacketByName(bp, "failsafeBrakingStrength"))
		ch->failsafeBrakingStrength = getBridgePacketDoubleByName(bp, "failsafeBrakingStrength");
	if (hasBridgePacketByName(bp, "failsafeCurrentLimit"))
		ch->failsafeCurrentLimit = getBridgePacketDoubleByName(bp, "failsafeCurrentLimit");
	if (hasBridgePacketByName(bp, "minFailsafeTime"))
		ch->minFailsafeTime = getBridgePacketUInt32ByName(bp, "minFailsafeTime");
	if (hasBridgePacketByName(bp, "maxFailsafeTime"))
		ch->maxFailsafeTime = getBridgePacketUInt32ByName(bp, "maxFailsafeTime");
	if (hasBridgePacketByName(bp, "inductance"))
		ch->inductance = getBridgePacketDoubleByName(bp, "inductance");
	if (hasBridgePacketByName(bp, "minInductance"))
		ch->minInductance = getBridgePacketDoubleByName(bp, "minInductance");
	if (hasBridgePacketByName(bp, "maxInductance"))
		ch->maxInductance = getBridgePacketDoubleByName(bp, "maxInductance");
	if (hasBridgePacketByName(bp, "kd"))
		ch->kd = getBridgePacketDoubleByName(bp, "kd");
	if (hasBridgePacketByName(bp, "ki"))
		ch->ki = getBridgePacketDoubleByName(bp, "ki");
	if (hasBridgePacketByName(bp, "kp"))
		ch->kp = getBridgePacketDoubleByName(bp, "kp");
	if (hasBridgePacketByName(bp, "positionType"))
		ch->positionType = getBridgePacketInt32ByName(bp, "positionType");
	if (hasBridgePacketByName(bp, "rescaleFactor"))
		ch->rescaleFactor = getBridgePacketDoubleByName(bp, "rescaleFactor");
	if (hasBridgePacketByName(bp, "stallVelocity"))
		ch->stallVelocity = getBridgePacketDoubleByName(bp, "stallVelocity");
	if (hasBridgePacketByName(bp, "minStallVelocity"))
		ch->minStallVelocity = getBridgePacketDoubleByName(bp, "minStallVelocity");
	if (hasBridgePacketByName(bp, "maxStallVelocity"))
		ch->maxStallVelocity = getBridgePacketDoubleByName(bp, "maxStallVelocity");
	if (hasBridgePacketByName(bp, "surgeCurrentLimit"))
		ch->surgeCurrentLimit = getBridgePacketDoubleByName(bp, "surgeCurrentLimit");
	if (hasBridgePacketByName(bp, "minSurgeCurrentLimit"))
		ch->minSurgeCurrentLimit = getBridgePacketDoubleByName(bp, "minSurgeCurrentLimit");
	if (hasBridgePacketByName(bp, "maxSurgeCurrentLimit"))
		ch->maxSurgeCurrentLimit = getBridgePacketDoubleByName(bp, "maxSurgeCurrentLimit");
	if (hasBridgePacketByName(bp, "targetVelocity"))
		ch->targetVelocity = getBridgePacketDoubleByName(bp, "targetVelocity");
	if (hasBridgePacketByName(bp, "minTargetVelocity"))
		ch->minTargetVelocity = getBridgePacketDoubleByName(bp, "minTargetVelocity");
	if (hasBridgePacketByName(bp, "maxTargetVelocity"))
		ch->maxTargetVelocity = getBridgePacketDoubleByName(bp, "maxTargetVelocity");
	if (hasBridgePacketByName(bp, "velocity"))
		ch->velocity = getBridgePacketDoubleByName(bp, "velocity");

	return (EPHIDGET_OK);
}

static PhidgetReturnCode CCONV
_getStatus(PhidgetChannelHandle phid, BridgePacket **bp) {
	PhidgetMotorVelocityControllerHandle ch;

	ch = (PhidgetMotorVelocityControllerHandle)phid;

	return (createBridgePacket(bp, BP_SETSTATUS, 43, "_class_version_=%u"
	  ",acceleration=%g"
	  ",minAcceleration=%g"
	  ",maxAcceleration=%g"
	  ",activeCurrentLimit=%g"
	  ",minBrakingStrength=%g"
	  ",maxBrakingStrength=%g"
	  ",currentLimit=%g"
	  ",minCurrentLimit=%g"
	  ",maxCurrentLimit=%g"
	  ",dataInterval=%u"
	  ",minDataInterval=%u"
	  ",maxDataInterval=%u"
	  ",dataIntervalDbl=%g"
	  ",minDataRate=%g"
	  ",maxDataRate=%g"
	  ",deadBand=%g"
	  ",dutyCycle=%g"
	  ",engaged=%d"
	  ",expectedVelocity=%g"
	  ",enableExpectedVelocity=%d"
	  ",failsafeBrakingStrength=%g"
	  ",failsafeCurrentLimit=%g"
	  ",minFailsafeTime=%u"
	  ",maxFailsafeTime=%u"
	  ",inductance=%g"
	  ",minInductance=%g"
	  ",maxInductance=%g"
	  ",kd=%g"
	  ",ki=%g"
	  ",kp=%g"
	  ",positionType=%d"
	  ",rescaleFactor=%g"
	  ",stallVelocity=%g"
	  ",minStallVelocity=%g"
	  ",maxStallVelocity=%g"
	  ",surgeCurrentLimit=%g"
	  ",minSurgeCurrentLimit=%g"
	  ",maxSurgeCurrentLimit=%g"
	  ",targetVelocity=%g"
	  ",minTargetVelocity=%g"
	  ",maxTargetVelocity=%g"
	  ",velocity=%g"
	  ,1 /* class version */
	  ,ch->acceleration
	  ,ch->minAcceleration
	  ,ch->maxAcceleration
	  ,ch->activeCurrentLimit
	  ,ch->minBrakingStrength
	  ,ch->maxBrakingStrength
	  ,ch->currentLimit
	  ,ch->minCurrentLimit
	  ,ch->maxCurrentLimit
	  ,(uint32_t)round(ch->dataInterval)
	  ,ch->minDataInterval
	  ,ch->maxDataInterval
	  ,ch->dataInterval
	  ,ch->minDataRate
	  ,ch->maxDataRate
	  ,ch->deadBand
	  ,ch->dutyCycle
	  ,ch->engaged
	  ,ch->expectedVelocity
	  ,ch->enableExpectedVelocity
	  ,ch->failsafeBrakingStrength
	  ,ch->failsafeCurrentLimit
	  ,ch->minFailsafeTime
	  ,ch->maxFailsafeTime
	  ,ch->inductance
	  ,ch->minInductance
	  ,ch->maxInductance
	  ,ch->kd
	  ,ch->ki
	  ,ch->kp
	  ,ch->positionType
	  ,ch->rescaleFactor
	  ,ch->stallVelocity
	  ,ch->minStallVelocity
	  ,ch->maxStallVelocity
	  ,ch->surgeCurrentLimit
	  ,ch->minSurgeCurrentLimit
	  ,ch->maxSurgeCurrentLimit
	  ,ch->targetVelocity
	  ,ch->minTargetVelocity
	  ,ch->maxTargetVelocity
	  ,ch->velocity
	));
}

static PhidgetReturnCode CCONV
_bridgeInput(PhidgetChannelHandle phid, BridgePacket *bp) {
	PhidgetMotorVelocityControllerHandle ch;
	PhidgetReturnCode res;

	ch = (PhidgetMotorVelocityControllerHandle)phid;
	res = EPHIDGET_OK;

	switch (bp->vpkt) {
	case BP_SETFAILSAFETIME:
		res = DEVBRIDGEINPUT(phid, bp);
		break;
	case BP_FAILSAFERESET:
		res = DEVBRIDGEINPUT(phid, bp);
		break;
	case BP_SETACCELERATION:
		TESTRANGE_IOP(bp->iop, "%lf", getBridgePacketDouble(bp, 0), ch->minAcceleration,
		  ch->maxAcceleration);
		res = DEVBRIDGEINPUT(phid, bp);
		if (res != EPHIDGET_OK)
			break;
		ch->acceleration = getBridgePacketDouble(bp, 0);
		if (bridgePacketIsFromNet(bp)) {
			FIRE_PROPERTYCHANGE(ch, "Acceleration");
		}
		break;
	case BP_SETCURRENTLIMIT:
		TESTRANGE_IOP(bp->iop, "%lf", getBridgePacketDouble(bp, 0), ch->minCurrentLimit,
		  ch->maxCurrentLimit);
		res = DEVBRIDGEINPUT(phid, bp);
		if (res != EPHIDGET_OK)
			break;
		ch->currentLimit = getBridgePacketDouble(bp, 0);
		if (bridgePacketIsFromNet(bp)) {
			FIRE_PROPERTYCHANGE(ch, "CurrentLimit");
		}
		break;
	case BP_SETDATAINTERVAL:
		if (bp->entrycnt > 1)
			TESTRANGE_IOP(bp->iop, "%lf", round_double((1000.0 / getBridgePacketDouble(bp, 1)), 4),
			  ch->minDataRate, ch->maxDataRate);
		else
			TESTRANGE_IOP(bp->iop, "%"PRIu32, getBridgePacketUInt32(bp, 0), ch->minDataInterval,
			  ch->maxDataInterval);
		res = DEVBRIDGEINPUT(phid, bp);
		if (res != EPHIDGET_OK)
			break;
		if (bp->entrycnt > 1)
			ch->dataInterval = getBridgePacketDouble(bp, 1);
		else
			ch->dataInterval = (double)getBridgePacketUInt32(bp, 0);
		if (bridgePacketIsFromNet(bp)) {
			FIRE_PROPERTYCHANGE(ch, "DataInterval");
			FIRE_PROPERTYCHANGE(ch, "DataRate");
		}
		break;
	case BP_SETDEADBAND:
		res = DEVBRIDGEINPUT(phid, bp);
		if (res != EPHIDGET_OK)
			break;
		ch->deadBand = getBridgePacketDouble(bp, 0);
		if (bridgePacketIsFromNet(bp)) {
			FIRE_PROPERTYCHANGE(ch, "DeadBand");
		}
		break;
	case BP_SETENGAGED:
		TESTBOOL_IOP(bp->iop, getBridgePacketInt32(bp, 0));
		res = DEVBRIDGEINPUT(phid, bp);
		if (res != EPHIDGET_OK)
			break;
		ch->engaged = getBridgePacketInt32(bp, 0);
		if (bridgePacketIsFromNet(bp)) {
			FIRE_PROPERTYCHANGE(ch, "Engaged");
		}
		break;
	case BP_SETENABLEEXPECTEDVELOCITY:
		TESTBOOL_IOP(bp->iop, getBridgePacketInt32(bp, 0));
		res = DEVBRIDGEINPUT(phid, bp);
		if (res != EPHIDGET_OK)
			break;
		ch->enableExpectedVelocity = getBridgePacketInt32(bp, 0);
		if (bridgePacketIsFromNet(bp)) {
			FIRE_PROPERTYCHANGE(ch, "EnableExpectedVelocity");
		}
		break;
	case BP_SETFAILSAFEBRAKINGDUTYCYCLE:
		res = DEVBRIDGEINPUT(phid, bp);
		if (res != EPHIDGET_OK)
			break;
		ch->failsafeBrakingStrength = getBridgePacketDouble(bp, 0);
		if (bridgePacketIsFromNet(bp)) {
			FIRE_PROPERTYCHANGE(ch, "FailsafeBrakingStrength");
		}
		break;
	case BP_SETFAILSAFECURRENTLIMIT:
		res = DEVBRIDGEINPUT(phid, bp);
		if (res != EPHIDGET_OK)
			break;
		ch->failsafeCurrentLimit = getBridgePacketDouble(bp, 0);
		if (bridgePacketIsFromNet(bp)) {
			FIRE_PROPERTYCHANGE(ch, "FailsafeCurrentLimit");
		}
		break;
	case BP_SETINDUCTANCE:
		TESTRANGE_IOP(bp->iop, "%lf", getBridgePacketDouble(bp, 0), ch->minInductance,
		  ch->maxInductance);
		res = DEVBRIDGEINPUT(phid, bp);
		if (res != EPHIDGET_OK)
			break;
		ch->inductance = getBridgePacketDouble(bp, 0);
		if (bridgePacketIsFromNet(bp)) {
			FIRE_PROPERTYCHANGE(ch, "Inductance");
		}
		break;
	case BP_SETKD:
		res = DEVBRIDGEINPUT(phid, bp);
		if (res != EPHIDGET_OK)
			break;
		ch->kd = getBridgePacketDouble(bp, 0);
		if (bridgePacketIsFromNet(bp)) {
			FIRE_PROPERTYCHANGE(ch, "Kd");
		}
		break;
	case BP_SETKI:
		res = DEVBRIDGEINPUT(phid, bp);
		if (res != EPHIDGET_OK)
			break;
		ch->ki = getBridgePacketDouble(bp, 0);
		if (bridgePacketIsFromNet(bp)) {
			FIRE_PROPERTYCHANGE(ch, "Ki");
		}
		break;
	case BP_SETKP:
		res = DEVBRIDGEINPUT(phid, bp);
		if (res != EPHIDGET_OK)
			break;
		ch->kp = getBridgePacketDouble(bp, 0);
		if (bridgePacketIsFromNet(bp)) {
			FIRE_PROPERTYCHANGE(ch, "Kp");
		}
		break;
	case BP_POSITIONTYPE:
		if (!supportedPositionType(phid, (Phidget_PositionType)getBridgePacketInt32(bp, 0)))
			return (MOS_ERROR(bp->iop, EPHIDGET_INVALIDARG,
			  "Specified PositionType is unsupported by this device."));
		res = DEVBRIDGEINPUT(phid, bp);
		if (res != EPHIDGET_OK)
			break;
		ch->positionType = getBridgePacketInt32(bp, 0);
		if (bridgePacketIsFromNet(bp)) {
			FIRE_PROPERTYCHANGE(ch, "PositionType");
		}
		break;
	case BP_SETSTALLVELOCITY:
		TESTRANGE_IOP(bp->iop, "%lf", getBridgePacketDouble(bp, 0), ch->minStallVelocity,
		  ch->maxStallVelocity);
		res = DEVBRIDGEINPUT(phid, bp);
		if (res != EPHIDGET_OK)
			break;
		ch->stallVelocity = getBridgePacketDouble(bp, 0);
		if (bridgePacketIsFromNet(bp)) {
			FIRE_PROPERTYCHANGE(ch, "StallVelocity");
		}
		break;
	case BP_SETSURGECURRENTLIMIT:
		TESTRANGE_IOP(bp->iop, "%lf", getBridgePacketDouble(bp, 0), ch->minSurgeCurrentLimit,
		  ch->maxSurgeCurrentLimit);
		res = DEVBRIDGEINPUT(phid, bp);
		if (res != EPHIDGET_OK)
			break;
		ch->surgeCurrentLimit = getBridgePacketDouble(bp, 0);
		if (bridgePacketIsFromNet(bp)) {
			FIRE_PROPERTYCHANGE(ch, "SurgeCurrentLimit");
		}
		break;
	case BP_SETDUTYCYCLE:
		TESTRANGE_IOP(bp->iop, "%lf", getBridgePacketDouble(bp, 0), ch->minTargetVelocity,
		  ch->maxTargetVelocity);
		res = DEVBRIDGEINPUT(phid, bp);
		if (res != EPHIDGET_OK)
			break;
		ch->targetVelocity = getBridgePacketDouble(bp, 0);
		if (bridgePacketIsFromNet(bp)) {
			FIRE_PROPERTYCHANGE(ch, "TargetVelocity");
		}
		break;
	case BP_DUTYCYCLECHANGE:
		ch->dutyCycle = getBridgePacketDouble(bp, 0);
		FIRECH(ch, DutyCycleUpdate, ch->dutyCycle);
		break;
	default:
		logerr("%"PRIphid": unsupported bridge packet:0x%x", phid, bp->vpkt);
		res = EPHIDGET_UNSUPPORTED;
	}

	return (res);
}

static PhidgetReturnCode CCONV
_initAfterOpen(PhidgetChannelHandle phid) {
	PhidgetReturnCode ret;

	TESTPTR(phid);

	ret = EPHIDGET_OK;


	switch (phid->UCD->uid) {
	default:
		MOS_PANIC("Unsupported Channel");
	}


	return (ret);
}

static PhidgetReturnCode CCONV
_setDefaults(PhidgetChannelHandle phid) {
	PhidgetReturnCode ret;

	TESTPTR(phid);

	ret = EPHIDGET_OK;

	switch (phid->UCD->uid) {
	default:
		MOS_PANIC("Unsupported Channel");
	}

	return (ret);
}

static void CCONV
_fireInitialEvents(PhidgetChannelHandle phid) {
	PhidgetMotorVelocityControllerHandle ch;

	ch = (PhidgetMotorVelocityControllerHandle)phid;

	if(ch->dutyCycle != PUNK_DBL)
		FIRECH(ch, DutyCycleUpdate, ch->dutyCycle);

}

static int CCONV
_hasInitialState(PhidgetChannelHandle phid) {
	PhidgetMotorVelocityControllerHandle ch;

	ch = (PhidgetMotorVelocityControllerHandle)phid;

	if(ch->dutyCycle == PUNK_DBL)
		return (PFALSE);

	return (PTRUE);
}

static void CCONV
_free(PhidgetChannelHandle *ch) {

	mos_free(*ch, sizeof (struct _PhidgetMotorVelocityController));
}

static PhidgetReturnCode CCONV
_create(PhidgetMotorVelocityControllerHandle *phidp) {

	CHANNELCREATE_BODY(MotorVelocityController, PHIDCHCLASS_MOTORVELOCITYCONTROLLER);
	return (EPHIDGET_OK);
}

API_PRETURN
PhidgetMotorVelocityController_delete(PhidgetMotorVelocityControllerHandle *phidp) {

	return (Phidget_delete((PhidgetHandle *)phidp));
}

API_PRETURN
PhidgetMotorVelocityController_enableFailsafe(PhidgetMotorVelocityControllerHandle ch,
  uint32_t failsafeTime) {

	TESTPTR_PR(ch);
	TESTCHANNELCLASS_PR(ch, PHIDCHCLASS_MOTORVELOCITYCONTROLLER);
	TESTATTACHED_PR(ch);

	return bridgeSendToDevice((PhidgetChannelHandle)ch, BP_SETFAILSAFETIME, NULL, NULL, 1, "%u",
	  failsafeTime); 
}

API_PRETURN
PhidgetMotorVelocityController_resetFailsafe(PhidgetMotorVelocityControllerHandle ch) {

	TESTPTR_PR(ch);
	TESTCHANNELCLASS_PR(ch, PHIDCHCLASS_MOTORVELOCITYCONTROLLER);
	TESTATTACHED_PR(ch);

	return bridgeSendToDevice((PhidgetChannelHandle)ch, BP_FAILSAFERESET, NULL, NULL, 0, NULL); 
}

API_PRETURN
PhidgetMotorVelocityController_getActiveCurrentLimit(PhidgetMotorVelocityControllerHandle ch,
  double *activeCurrentLimit) {

	TESTPTR_PR(ch);
	TESTPTR_PR(activeCurrentLimit);
	TESTCHANNELCLASS_PR(ch, PHIDCHCLASS_MOTORVELOCITYCONTROLLER);
	TESTATTACHED_PR(ch);

	*activeCurrentLimit = ch->activeCurrentLimit;
	if (ch->activeCurrentLimit == (double)PUNK_DBL)
		return (PHID_RETURN(EPHIDGET_UNKNOWNVAL));
	return (EPHIDGET_OK);
}

API_PRETURN
PhidgetMotorVelocityController_getMinBrakingStrength(PhidgetMotorVelocityControllerHandle ch,
  double *minBrakingStrength) {

	TESTPTR_PR(ch);
	TESTPTR_PR(minBrakingStrength);
	TESTCHANNELCLASS_PR(ch, PHIDCHCLASS_MOTORVELOCITYCONTROLLER);
	TESTATTACHED_PR(ch);

	*minBrakingStrength = ch->minBrakingStrength;
	if (ch->minBrakingStrength == (double)PUNK_DBL)
		return (PHID_RETURN(EPHIDGET_UNKNOWNVAL));
	return (EPHIDGET_OK);
}

API_PRETURN
PhidgetMotorVelocityController_getMaxBrakingStrength(PhidgetMotorVelocityControllerHandle ch,
  double *maxBrakingStrength) {

	TESTPTR_PR(ch);
	TESTPTR_PR(maxBrakingStrength);
	TESTCHANNELCLASS_PR(ch, PHIDCHCLASS_MOTORVELOCITYCONTROLLER);
	TESTATTACHED_PR(ch);

	*maxBrakingStrength = ch->maxBrakingStrength;
	if (ch->maxBrakingStrength == (double)PUNK_DBL)
		return (PHID_RETURN(EPHIDGET_UNKNOWNVAL));
	return (EPHIDGET_OK);
}

API_PRETURN
PhidgetMotorVelocityController_setCurrentLimit(PhidgetMotorVelocityControllerHandle ch,
  double currentLimit) {

	TESTPTR_PR(ch);
	TESTCHANNELCLASS_PR(ch, PHIDCHCLASS_MOTORVELOCITYCONTROLLER);
	TESTATTACHED_PR(ch);

	return (bridgeSendToDevice((PhidgetChannelHandle)ch, BP_SETCURRENTLIMIT, NULL, NULL, 1, "%g",
	  currentLimit));
}

API_PRETURN
PhidgetMotorVelocityController_getCurrentLimit(PhidgetMotorVelocityControllerHandle ch,
  double *currentLimit) {

	TESTPTR_PR(ch);
	TESTPTR_PR(currentLimit);
	TESTCHANNELCLASS_PR(ch, PHIDCHCLASS_MOTORVELOCITYCONTROLLER);
	TESTATTACHED_PR(ch);

	*currentLimit = ch->currentLimit;
	if (ch->currentLimit == (double)PUNK_DBL)
		return (PHID_RETURN(EPHIDGET_UNKNOWNVAL));
	return (EPHIDGET_OK);
}

API_PRETURN
PhidgetMotorVelocityController_getMinCurrentLimit(PhidgetMotorVelocityControllerHandle ch,
  double *minCurrentLimit) {

	TESTPTR_PR(ch);
	TESTPTR_PR(minCurrentLimit);
	TESTCHANNELCLASS_PR(ch, PHIDCHCLASS_MOTORVELOCITYCONTROLLER);
	TESTATTACHED_PR(ch);

	*minCurrentLimit = ch->minCurrentLimit;
	if (ch->minCurrentLimit == (double)PUNK_DBL)
		return (PHID_RETURN(EPHIDGET_UNKNOWNVAL));
	return (EPHIDGET_OK);
}

API_PRETURN
PhidgetMotorVelocityController_getMaxCurrentLimit(PhidgetMotorVelocityControllerHandle ch,
  double *maxCurrentLimit) {

	TESTPTR_PR(ch);
	TESTPTR_PR(maxCurrentLimit);
	TESTCHANNELCLASS_PR(ch, PHIDCHCLASS_MOTORVELOCITYCONTROLLER);
	TESTATTACHED_PR(ch);

	*maxCurrentLimit = ch->maxCurrentLimit;
	if (ch->maxCurrentLimit == (double)PUNK_DBL)
		return (PHID_RETURN(EPHIDGET_UNKNOWNVAL));
	return (EPHIDGET_OK);
}

API_PRETURN
PhidgetMotorVelocityController_setDataInterval(PhidgetMotorVelocityControllerHandle ch,
  uint32_t dataInterval) {

	TESTPTR_PR(ch);
	TESTCHANNELCLASS_PR(ch, PHIDCHCLASS_MOTORVELOCITYCONTROLLER);
	TESTATTACHED_PR(ch);

	return (bridgeSendToDevice((PhidgetChannelHandle)ch, BP_SETDATAINTERVAL, NULL, NULL, 1, "%u",
	  dataInterval));
}

API_PRETURN
PhidgetMotorVelocityController_getDataInterval(PhidgetMotorVelocityControllerHandle ch,
  uint32_t *dataInterval) {

	TESTPTR_PR(ch);
	TESTPTR_PR(dataInterval);
	TESTCHANNELCLASS_PR(ch, PHIDCHCLASS_MOTORVELOCITYCONTROLLER);
	TESTATTACHED_PR(ch);

	*dataInterval = (uint32_t)round(ch->dataInterval);
	if (ch->dataInterval == (double)PUNK_DBL)
		return (PHID_RETURN(EPHIDGET_UNKNOWNVAL));
	return (EPHIDGET_OK);
}

API_PRETURN
PhidgetMotorVelocityController_getMinDataInterval(PhidgetMotorVelocityControllerHandle ch,
  uint32_t *minDataInterval) {

	TESTPTR_PR(ch);
	TESTPTR_PR(minDataInterval);
	TESTCHANNELCLASS_PR(ch, PHIDCHCLASS_MOTORVELOCITYCONTROLLER);
	TESTATTACHED_PR(ch);

	*minDataInterval = ch->minDataInterval;
	if (ch->minDataInterval == (uint32_t)PUNK_UINT32)
		return (PHID_RETURN(EPHIDGET_UNKNOWNVAL));
	return (EPHIDGET_OK);
}

API_PRETURN
PhidgetMotorVelocityController_getMaxDataInterval(PhidgetMotorVelocityControllerHandle ch,
  uint32_t *maxDataInterval) {

	TESTPTR_PR(ch);
	TESTPTR_PR(maxDataInterval);
	TESTCHANNELCLASS_PR(ch, PHIDCHCLASS_MOTORVELOCITYCONTROLLER);
	TESTATTACHED_PR(ch);

	*maxDataInterval = ch->maxDataInterval;
	if (ch->maxDataInterval == (uint32_t)PUNK_UINT32)
		return (PHID_RETURN(EPHIDGET_UNKNOWNVAL));
	return (EPHIDGET_OK);
}

API_PRETURN
PhidgetMotorVelocityController_setDataRate(PhidgetMotorVelocityControllerHandle ch, double dataRate) {

	TESTPTR_PR(ch);
	TESTCHANNELCLASS_PR(ch, PHIDCHCLASS_MOTORVELOCITYCONTROLLER);
	TESTATTACHED_PR(ch);

	return bridgeSendToDevice((PhidgetChannelHandle)ch, BP_SETDATAINTERVAL, NULL, NULL, 2, "%u%g",
	  (uint32_t)round(1000.0 / dataRate), (double)(1000.0 / dataRate));
}

API_PRETURN
PhidgetMotorVelocityController_getDataRate(PhidgetMotorVelocityControllerHandle ch, double *dataRate) {

	TESTPTR_PR(ch);
	TESTPTR_PR(dataRate);
	TESTCHANNELCLASS_PR(ch, PHIDCHCLASS_MOTORVELOCITYCONTROLLER);
	TESTATTACHED_PR(ch);

	*dataRate = round_double((1000.0 / ch->dataInterval), 4);
	if (ch->dataInterval == (double)PUNK_DBL)
		return (PHID_RETURN(EPHIDGET_UNKNOWNVAL));
	return (EPHIDGET_OK);
}

API_PRETURN
PhidgetMotorVelocityController_getMinDataRate(PhidgetMotorVelocityControllerHandle ch,
  double *minDataRate) {

	TESTPTR_PR(ch);
	TESTPTR_PR(minDataRate);
	TESTCHANNELCLASS_PR(ch, PHIDCHCLASS_MOTORVELOCITYCONTROLLER);
	TESTATTACHED_PR(ch);

	*minDataRate = ch->minDataRate;
	if (ch->minDataRate == (double)PUNK_DBL)
		return (PHID_RETURN(EPHIDGET_UNKNOWNVAL));
	return (EPHIDGET_OK);
}

API_PRETURN
PhidgetMotorVelocityController_getMaxDataRate(PhidgetMotorVelocityControllerHandle ch,
  double *maxDataRate) {

	TESTPTR_PR(ch);
	TESTPTR_PR(maxDataRate);
	TESTCHANNELCLASS_PR(ch, PHIDCHCLASS_MOTORVELOCITYCONTROLLER);
	TESTATTACHED_PR(ch);

	*maxDataRate = ch->maxDataRate;
	if (ch->maxDataRate == (double)PUNK_DBL)
		return (PHID_RETURN(EPHIDGET_UNKNOWNVAL));
	return (EPHIDGET_OK);
}

API_PRETURN
PhidgetMotorVelocityController_getDutyCycle(PhidgetMotorVelocityControllerHandle ch,
  double *dutyCycle) {

	TESTPTR_PR(ch);
	TESTPTR_PR(dutyCycle);
	TESTCHANNELCLASS_PR(ch, PHIDCHCLASS_MOTORVELOCITYCONTROLLER);
	TESTATTACHED_PR(ch);

	*dutyCycle = ch->dutyCycle;
	if (ch->dutyCycle == (double)PUNK_DBL)
		return (PHID_RETURN(EPHIDGET_UNKNOWNVAL));
	return (EPHIDGET_OK);
}

API_PRETURN
PhidgetMotorVelocityController_setEngaged(PhidgetMotorVelocityControllerHandle ch, int engaged) {

	TESTPTR_PR(ch);
	TESTCHANNELCLASS_PR(ch, PHIDCHCLASS_MOTORVELOCITYCONTROLLER);
	TESTATTACHED_PR(ch);

	return (bridgeSendToDevice((PhidgetChannelHandle)ch, BP_SETENGAGED, NULL, NULL, 1, "%d", engaged));
}

API_PRETURN
PhidgetMotorVelocityController_getEngaged(PhidgetMotorVelocityControllerHandle ch, int *engaged) {

	TESTPTR_PR(ch);
	TESTPTR_PR(engaged);
	TESTCHANNELCLASS_PR(ch, PHIDCHCLASS_MOTORVELOCITYCONTROLLER);
	TESTATTACHED_PR(ch);

	*engaged = ch->engaged;
	if (ch->engaged == (int)PUNK_BOOL)
		return (PHID_RETURN(EPHIDGET_UNKNOWNVAL));
	return (EPHIDGET_OK);
}

API_PRETURN
PhidgetMotorVelocityController_setEnableExpectedVelocity(PhidgetMotorVelocityControllerHandle ch,
  int enableExpectedVelocity) {

	TESTPTR_PR(ch);
	TESTCHANNELCLASS_PR(ch, PHIDCHCLASS_MOTORVELOCITYCONTROLLER);
	TESTATTACHED_PR(ch);

	return (bridgeSendToDevice((PhidgetChannelHandle)ch, BP_SETENABLEEXPECTEDVELOCITY, NULL, NULL, 1,
	  "%d", enableExpectedVelocity));
}

API_PRETURN
PhidgetMotorVelocityController_getEnableExpectedVelocity(PhidgetMotorVelocityControllerHandle ch,
  int *enableExpectedVelocity) {

	TESTPTR_PR(ch);
	TESTPTR_PR(enableExpectedVelocity);
	TESTCHANNELCLASS_PR(ch, PHIDCHCLASS_MOTORVELOCITYCONTROLLER);
	TESTATTACHED_PR(ch);

	*enableExpectedVelocity = ch->enableExpectedVelocity;
	if (ch->enableExpectedVelocity == (int)PUNK_BOOL)
		return (PHID_RETURN(EPHIDGET_UNKNOWNVAL));
	return (EPHIDGET_OK);
}

API_PRETURN
PhidgetMotorVelocityController_setFailsafeBrakingStrength(PhidgetMotorVelocityControllerHandle ch,
  double failsafeBrakingStrength) {

	TESTPTR_PR(ch);
	TESTCHANNELCLASS_PR(ch, PHIDCHCLASS_MOTORVELOCITYCONTROLLER);
	TESTATTACHED_PR(ch);

	return (bridgeSendToDevice((PhidgetChannelHandle)ch, BP_SETFAILSAFEBRAKINGDUTYCYCLE, NULL, NULL, 1,
	  "%g", failsafeBrakingStrength));
}

API_PRETURN
PhidgetMotorVelocityController_getFailsafeBrakingStrength(PhidgetMotorVelocityControllerHandle ch,
  double *failsafeBrakingStrength) {

	TESTPTR_PR(ch);
	TESTPTR_PR(failsafeBrakingStrength);
	TESTCHANNELCLASS_PR(ch, PHIDCHCLASS_MOTORVELOCITYCONTROLLER);
	TESTATTACHED_PR(ch);

	*failsafeBrakingStrength = ch->failsafeBrakingStrength;
	if (ch->failsafeBrakingStrength == (double)PUNK_DBL)
		return (PHID_RETURN(EPHIDGET_UNKNOWNVAL));
	return (EPHIDGET_OK);
}

API_PRETURN
PhidgetMotorVelocityController_setFailsafeCurrentLimit(PhidgetMotorVelocityControllerHandle ch,
  double failsafeCurrentLimit) {

	TESTPTR_PR(ch);
	TESTCHANNELCLASS_PR(ch, PHIDCHCLASS_MOTORVELOCITYCONTROLLER);
	TESTATTACHED_PR(ch);

	return (bridgeSendToDevice((PhidgetChannelHandle)ch, BP_SETFAILSAFECURRENTLIMIT, NULL, NULL, 1, "%g",
	  failsafeCurrentLimit));
}

API_PRETURN
PhidgetMotorVelocityController_getFailsafeCurrentLimit(PhidgetMotorVelocityControllerHandle ch,
  double *failsafeCurrentLimit) {

	TESTPTR_PR(ch);
	TESTPTR_PR(failsafeCurrentLimit);
	TESTCHANNELCLASS_PR(ch, PHIDCHCLASS_MOTORVELOCITYCONTROLLER);
	TESTATTACHED_PR(ch);

	*failsafeCurrentLimit = ch->failsafeCurrentLimit;
	if (ch->failsafeCurrentLimit == (double)PUNK_DBL)
		return (PHID_RETURN(EPHIDGET_UNKNOWNVAL));
	return (EPHIDGET_OK);
}

API_PRETURN
PhidgetMotorVelocityController_getMinFailsafeTime(PhidgetMotorVelocityControllerHandle ch,
  uint32_t *minFailsafeTime) {

	TESTPTR_PR(ch);
	TESTPTR_PR(minFailsafeTime);
	TESTCHANNELCLASS_PR(ch, PHIDCHCLASS_MOTORVELOCITYCONTROLLER);
	TESTATTACHED_PR(ch);

	*minFailsafeTime = ch->minFailsafeTime;
	if (ch->minFailsafeTime == (uint32_t)PUNK_UINT32)
		return (PHID_RETURN(EPHIDGET_UNKNOWNVAL));
	return (EPHIDGET_OK);
}

API_PRETURN
PhidgetMotorVelocityController_getMaxFailsafeTime(PhidgetMotorVelocityControllerHandle ch,
  uint32_t *maxFailsafeTime) {

	TESTPTR_PR(ch);
	TESTPTR_PR(maxFailsafeTime);
	TESTCHANNELCLASS_PR(ch, PHIDCHCLASS_MOTORVELOCITYCONTROLLER);
	TESTATTACHED_PR(ch);

	*maxFailsafeTime = ch->maxFailsafeTime;
	if (ch->maxFailsafeTime == (uint32_t)PUNK_UINT32)
		return (PHID_RETURN(EPHIDGET_UNKNOWNVAL));
	return (EPHIDGET_OK);
}

API_PRETURN
PhidgetMotorVelocityController_setInductance(PhidgetMotorVelocityControllerHandle ch,
  double inductance) {

	TESTPTR_PR(ch);
	TESTCHANNELCLASS_PR(ch, PHIDCHCLASS_MOTORVELOCITYCONTROLLER);
	TESTATTACHED_PR(ch);

	return (bridgeSendToDevice((PhidgetChannelHandle)ch, BP_SETINDUCTANCE, NULL, NULL, 1, "%g",
	  inductance));
}

API_PRETURN
PhidgetMotorVelocityController_getInductance(PhidgetMotorVelocityControllerHandle ch,
  double *inductance) {

	TESTPTR_PR(ch);
	TESTPTR_PR(inductance);
	TESTCHANNELCLASS_PR(ch, PHIDCHCLASS_MOTORVELOCITYCONTROLLER);
	TESTATTACHED_PR(ch);

	*inductance = ch->inductance;
	if (ch->inductance == (double)PUNK_DBL)
		return (PHID_RETURN(EPHIDGET_UNKNOWNVAL));
	return (EPHIDGET_OK);
}

API_PRETURN
PhidgetMotorVelocityController_getMinInductance(PhidgetMotorVelocityControllerHandle ch,
  double *minInductance) {

	TESTPTR_PR(ch);
	TESTPTR_PR(minInductance);
	TESTCHANNELCLASS_PR(ch, PHIDCHCLASS_MOTORVELOCITYCONTROLLER);
	TESTATTACHED_PR(ch);

	*minInductance = ch->minInductance;
	if (ch->minInductance == (double)PUNK_DBL)
		return (PHID_RETURN(EPHIDGET_UNKNOWNVAL));
	return (EPHIDGET_OK);
}

API_PRETURN
PhidgetMotorVelocityController_getMaxInductance(PhidgetMotorVelocityControllerHandle ch,
  double *maxInductance) {

	TESTPTR_PR(ch);
	TESTPTR_PR(maxInductance);
	TESTCHANNELCLASS_PR(ch, PHIDCHCLASS_MOTORVELOCITYCONTROLLER);
	TESTATTACHED_PR(ch);

	*maxInductance = ch->maxInductance;
	if (ch->maxInductance == (double)PUNK_DBL)
		return (PHID_RETURN(EPHIDGET_UNKNOWNVAL));
	return (EPHIDGET_OK);
}

API_PRETURN
PhidgetMotorVelocityController_getRescaleFactor(PhidgetMotorVelocityControllerHandle ch,
  double *rescaleFactor) {

	TESTPTR_PR(ch);
	TESTPTR_PR(rescaleFactor);
	TESTCHANNELCLASS_PR(ch, PHIDCHCLASS_MOTORVELOCITYCONTROLLER);
	TESTATTACHED_PR(ch);

	*rescaleFactor = ch->rescaleFactor;
	if (ch->rescaleFactor == (double)PUNK_DBL)
		return (PHID_RETURN(EPHIDGET_UNKNOWNVAL));
	return (EPHIDGET_OK);
}

API_PRETURN
PhidgetMotorVelocityController_setSurgeCurrentLimit(PhidgetMotorVelocityControllerHandle ch,
  double surgeCurrentLimit) {

	TESTPTR_PR(ch);
	TESTCHANNELCLASS_PR(ch, PHIDCHCLASS_MOTORVELOCITYCONTROLLER);
	TESTATTACHED_PR(ch);

	return (bridgeSendToDevice((PhidgetChannelHandle)ch, BP_SETSURGECURRENTLIMIT, NULL, NULL, 1, "%g",
	  surgeCurrentLimit));
}

API_PRETURN
PhidgetMotorVelocityController_getSurgeCurrentLimit(PhidgetMotorVelocityControllerHandle ch,
  double *surgeCurrentLimit) {

	TESTPTR_PR(ch);
	TESTPTR_PR(surgeCurrentLimit);
	TESTCHANNELCLASS_PR(ch, PHIDCHCLASS_MOTORVELOCITYCONTROLLER);
	TESTATTACHED_PR(ch);

	*surgeCurrentLimit = ch->surgeCurrentLimit;
	if (ch->surgeCurrentLimit == (double)PUNK_DBL)
		return (PHID_RETURN(EPHIDGET_UNKNOWNVAL));
	return (EPHIDGET_OK);
}

API_PRETURN
PhidgetMotorVelocityController_getMinSurgeCurrentLimit(PhidgetMotorVelocityControllerHandle ch,
  double *minSurgeCurrentLimit) {

	TESTPTR_PR(ch);
	TESTPTR_PR(minSurgeCurrentLimit);
	TESTCHANNELCLASS_PR(ch, PHIDCHCLASS_MOTORVELOCITYCONTROLLER);
	TESTATTACHED_PR(ch);

	*minSurgeCurrentLimit = ch->minSurgeCurrentLimit;
	if (ch->minSurgeCurrentLimit == (double)PUNK_DBL)
		return (PHID_RETURN(EPHIDGET_UNKNOWNVAL));
	return (EPHIDGET_OK);
}

API_PRETURN
PhidgetMotorVelocityController_getMaxSurgeCurrentLimit(PhidgetMotorVelocityControllerHandle ch,
  double *maxSurgeCurrentLimit) {

	TESTPTR_PR(ch);
	TESTPTR_PR(maxSurgeCurrentLimit);
	TESTCHANNELCLASS_PR(ch, PHIDCHCLASS_MOTORVELOCITYCONTROLLER);
	TESTATTACHED_PR(ch);

	*maxSurgeCurrentLimit = ch->maxSurgeCurrentLimit;
	if (ch->maxSurgeCurrentLimit == (double)PUNK_DBL)
		return (PHID_RETURN(EPHIDGET_UNKNOWNVAL));
	return (EPHIDGET_OK);
}

API_PRETURN
PhidgetMotorVelocityController_setOnDutyCycleUpdateHandler(PhidgetMotorVelocityControllerHandle ch,
  PhidgetMotorVelocityController_OnDutyCycleUpdateCallback fptr, void *ctx) {

	TESTPTR_PR(ch);
	TESTCHANNELCLASS_PR(ch, PHIDCHCLASS_MOTORVELOCITYCONTROLLER);

	ch->DutyCycleUpdate = fptr;
	ch->DutyCycleUpdateCtx = ctx;

	return (EPHIDGET_OK);
}

API_PRETURN
PhidgetMotorVelocityController_setOnExpectedVelocityChangeHandler(PhidgetMotorVelocityControllerHandle ch,
  PhidgetMotorVelocityController_OnExpectedVelocityChangeCallback fptr, void *ctx) {

	TESTPTR_PR(ch);
	TESTCHANNELCLASS_PR(ch, PHIDCHCLASS_MOTORVELOCITYCONTROLLER);

	ch->ExpectedVelocityChange = fptr;
	ch->ExpectedVelocityChangeCtx = ctx;

	return (EPHIDGET_OK);
}

API_PRETURN
PhidgetMotorVelocityController_setOnVelocityChangeHandler(PhidgetMotorVelocityControllerHandle ch,
  PhidgetMotorVelocityController_OnVelocityChangeCallback fptr, void *ctx) {

	TESTPTR_PR(ch);
	TESTCHANNELCLASS_PR(ch, PHIDCHCLASS_MOTORVELOCITYCONTROLLER);

	ch->VelocityChange = fptr;
	ch->VelocityChangeCtx = ctx;

	return (EPHIDGET_OK);
}
