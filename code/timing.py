# timing.py

#    This is the code behind the paper The Effects of Fiscal Targets in a Monetary Union: a Multi-Country Agent Based-Stock Flow Consistent Model
#    Copyright (C) 2017  Alessandro Caiani, Ermanno Catullo, Mauro Gallegati.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.


# flake8: noqa
from parameter import *
from initialize import *
from firm import *
from consumer import *
from matchingConsumption import *
from matchingLaborCapital import *
from enterExit import *
from aggregator import *
#from aggregatorAle import *
from time import *
import random
import os
import glob
import csv
from bank import *
from matchingCredit import *
from matchingBonds import *
from matchingDeposit import *
from globalInnovation import *
from printParameters import *
from centralBankUnion import *
from policy import *
from llm_runtime import configure as configure_llm


_LOG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'timing.log'))


def _flag(value):
    return 'on' if value else 'off'


def log_llm_toggles(parameter):
    """Append the current LLM toggle configuration to timing.log."""

    timestamp = strftime('%Y-%m-%d %H:%M:%S', localtime())
    line = (
        '[%s] LLM toggles server=%s timeout_ms=%s batch=%s firm=%s bank=%s wage=%s\n'
        % (
            timestamp,
            parameter.llm_server_url,
            parameter.llm_timeout_ms,
            _flag(parameter.llm_batch),
            _flag(parameter.use_llm_firm_pricing),
            _flag(parameter.use_llm_bank_credit),
            _flag(parameter.use_llm_wage),
        )
    )
    try:
        handle = open(_LOG_PATH, 'a')
        handle.write(line)
        handle.close()
    except Exception as exc:
        print 'Warning: failed to write LLM toggle log (%s)' % exc
    print line.strip()



def run_simulation(parameter=None, progress=True):
    # parameter
    para = parameter or Parameter()
    para.directory()
    log_llm_toggles(para)
    printPa=PrintParameters(para.name,para.folder)
    configure_llm(para)

    for run in para.Lrun:
        if para.weSeedRun=='yes':
           random.seed(run) 
        # initialization
        printPa.printingPara(para,run)
        ite=Initialize(para.ncountry,para.nconsumer,para.A,para.phi,\
                       para.beta,para.folder,para.name,run,para.delta,\
                       para.taxRatio,para.rDiscount,para.G,\
                       para.cDisposableIncome,para.cWealth,para.liqPref,para.rDeposit,para.rBonds,\
                       para.upsilon,para.maxPublicDeficit,para.xiBonds,para.ls,para.taxRatioMin,\
                       para.taxRatioMax,para.gMin,para.gMax,para.w0,para.wBar,para.upsilon2) 
        ite.createCentralBank()
        ite.createConsumer() 
        ite.createBasic()
        ite.createEtat()  
        name=para.name+'r'+str(run)
        gloInnovation=GlobalInnovation(ite.Lcountry,para.phi)

        enEx=enterExit(ite.Lcountry,ite.McountryFirmMaxNumber,\
                      para.folder,para.name,run,para.delta,para.A,\
                      ite.McountryBankMaxNumber,para.probBank,para.minReserve,\
                      para.rDiscount,para.xi,para.dividendRate,para.iota,para.rDeposit,\
                      para.upsilon,para.gamma,para.deltaInnovation,para.mu1,\
                      para.propTradable,para.Fcost,para.ni,para.minMarkUp,\
                      para.iotaE,para.theta,para.sigma,para.upsilon2,para.jobDuration)


        maConsumption=MatchingConsumption(ite.Lcountry,para.bound,para.propTradable)
        maLaborCapital=MatchingLaborCapital(para.bound)
        aggrega=Aggregator(ite.Lcountry,name,para.folder,para.timeCollectingStart,\
                                para.LtimeCollecting,para.printAgent)
        maCredit=MatchingCredit() 
        maBonds=MatchingBonds()
        maDeposit=MatchingDeposit(ite.Lcountry)  
        aggrega.basicL(ite.McountryConsumer) 
        centralBankUnion=CentralBankUnion(para.rDiscount,para.rDeposit,para.zeta,para.rBar,para.csi,para.csiDP,para.inflationTarget)
        maDeposit.creatingAccount(ite.McountryConsumer,ite.McountryFirm,ite.McountryBank,ite.McountryCentralBank) 
        poli=policy(para.startingPolicy,para.policyKind,para.maxPublicDeficitAusterity,\
                    para.maxPublicDeficit,para.upsilonConsumer,para.deltaLaborPolicy,ite.Lcountry,para.k,para.epsilon)


        # here we go
        for t in range(para.ncycle):
            print 
            print 'name ', para.name, '---- run', run, ' --- t ',  t

            maLaborCapital.bargaining(ite.McountryFirm,ite.McountryConsumer,\
                                 aggrega.McountryUnemployement,aggrega.McountryPastUnemployement,aggrega.McountryYL,aggrega.McountryPastYL,t)

            for country in ite.McountryFirm:
                for firm_key in ite.McountryFirm[country]: 
                    firm_obj = ite.McountryFirm[country][firm_key]
                    firm_obj.llm_tick = t
                    firm_obj.learning()  
                    #firm_obj.wageOffered(aggrega.McountryAvPrice,\
                    #                   aggrega.McountryUnemployement,para.nconsumer,aggrega.DcountryAvWage)          
                    firm_obj.productionDesired(ite.McountryBank,ite.McountryCentralBank,t,aggrega.McountryAvPrice)

            for country in ite.McountryBank:
                for bank_key in ite.McountryBank[country]:
                    bank_obj = ite.McountryBank[country][bank_key]
                    bank_obj.llm_tick = t

            maCredit.creditNetworkEvolution(ite.McountryFirm,ite.McountryBank,ite.McountryCentralBank,\
                                            gloInnovation.DglobalPhiNotTradable,gloInnovation.DglobalPhiTradable,aggrega.avPhiGlobalTradable)

            for country in ite.McountryBank: 
                for bank in ite.McountryBank[country]:
                    ite.McountryBank[country][bank].reservingCompulsory(ite.McountryCentralBank)

            maLaborCapital.working(ite.McountryFirm,ite.McountryConsumer,ite.McountryEtat,\
                                   ite.McountryBank,ite.McountryCentralBank,aggrega.McountryUnemployement)

            for country in ite.McountryFirm:
                for firm_key in ite.McountryFirm[country]: 
                    firm_obj = ite.McountryFirm[country][firm_key]
                    firm_obj.effectiveSelling(gloInnovation.DglobalPhiNotTradable,aggrega.avPhiGlobalTradable,\
                                               aggrega.avPriceGlobalTradable,aggrega.McountryAvPriceNotTradable,gloInnovation.DglobalPhi,aggrega.McountryAvPrice)

            for country in ite.McountryConsumer:
                for consumer in ite.McountryConsumer[country]:             
                    ite.McountryConsumer[country][consumer].income(ite.McountryBank,ite.McountryCentralBank)      

            for etat in ite.McountryEtat:
                ite.McountryEtat[etat].expectingTaxation(ite.McountryConsumer,ite.McountryCentralBank,aggrega.McountryUnemployement)

            poli.implementingPolicy(t,ite.McountryEtat,aggrega.McountryYReal,gloInnovation.DglobalPhi,aggrega.DcountryAvWage,\
                                    aggrega.McountryAvPrice,aggrega.McountryUnemployement,aggrega.DcumulativeDTBC,\
                                    aggrega.DcountryTradeBalance,ite.McountryConsumer,ite.McountryFirm,\
                                    enEx.DcountryUpsilon,enEx.DcountryJobDuration,aggrega.McountryDebtY,aggrega.McountryCumCA,\
                                    aggrega.McountryY,ite.McountryBank,enEx.DcountryIotaRelPhi) 

            for etat in ite.McountryEtat:
                ite.McountryEtat[etat].governmentPlannedExpenditure(ite.McountryConsumer,\
                                                      ite.McountryBank,ite.McountryCentralBank,\
                                                      aggrega.McountryAvPrice,aggrega.McountryY,t,\
                                                      aggrega.DcountryAvWage,poli.policy,\
                                                      aggrega.DcountryTradeBalance,aggrega.McountryUnemployement,gloInnovation.DglobalPhi)

            maBonds.allocatingBonds(ite.McountryBank,ite.McountryCentralBank,ite.McountryEtat) 

            for etat in ite.McountryEtat:
               ite.McountryEtat[etat].taxationConsumer(ite.McountryConsumer,ite.McountryBank,ite.McountryCentralBank) 

            for etat in ite.McountryEtat:
                ite.McountryEtat[etat].redistributionConsumer(ite.McountryConsumer,ite.McountryBank,ite.McountryCentralBank,aggrega.McountryAvPrice,t) 

            for country in ite.McountryConsumer:
                for consumer in ite.McountryConsumer[country]:
                    ite.McountryConsumer[country][consumer].consumptionDemand(ite.McountryBank,ite.McountryCentralBank,aggrega.DcountryFailureProbability) 

            maConsumption.consuming(ite.McountryConsumer,ite.McountryFirm,t,ite.McountryEtat,ite.McountryBank,ite.McountryCentralBank\
                                    ,aggrega.McountryAvPrice,aggrega.avPriceGlobalTradable,\
                                     aggrega.McountryAvPriceNotTradable)    

            for country in ite.McountryFirm:
                for firm in ite.McountryFirm[country]:
                    ite.McountryFirm[country][firm].changingInventory()   

            if para.printAgent=='yes':     
               for country in ite.McountryFirm:
                   for firm in ite.McountryFirm[country]:
                       ite.McountryFirm[country][firm].write(t,run)
               for country in ite.McountryBank:
                   for bank in ite.McountryBank[country]:  
                       ite.McountryBank[country][bank].write(t,run)

            aggrega.income(ite.McountryConsumer,t,\
                           run,ite.McountryFirm,ite.McountryEtat,ite.McountryBank,ite.McountryCentralBank,\
                           gloInnovation.DglobalPhi,enEx.DcountryFirmEnter,enEx.DcountryFirmExit,\
                           enEx.DcountryFirmEnterTradable,enEx.DcountryFirmExitTradable,\
                           enEx.DcountryBankEnter,enEx.DcountryBankExit,gloInnovation.DglobalPhiTradable,\
                           gloInnovation.DglobalPhiNotTradable,maCredit.creditCapitalInflow,maCredit.creditCapitalOutflow,
                           maBonds.creditBondInflow,maBonds.creditBondOutflow,enEx.DcountryEnterValue) 

            gloInnovation.spillover(ite.McountryFirm,t)

            for country in ite.McountryFirm:
                for firm in ite.McountryFirm[country]:
                    ite.McountryFirm[country][firm].existence(ite.McountryBank,ite.McountryCentralBank)

            for etat in ite.McountryEtat:
                ite.McountryEtat[etat].taxationFirm(ite.McountryFirm,ite.McountryBank,ite.McountryCentralBank)

            for country in ite.McountryFirm:
                for firm in ite.McountryFirm[country]:
                    ite.McountryFirm[country][firm].distributingDividends(ite.McountryConsumer,ite.McountryBank,ite.McountryCentralBank)

            enEx.exitFirm(ite.McountryFirm,ite.McountryBank,ite.McountryCentralBank)

            for country in ite.McountryBank:
                for bank in ite.McountryBank[country]:
                    ite.McountryBank[country][bank].existence(ite.McountryConsumer,ite.McountryFirm,\
                                          ite.McountryCentralBank,ite.McountryEtat[country].rBonds,ite.McountryEtat,aggrega.DcountryAvWage)

            for etat in ite.McountryEtat:
                ite.McountryEtat[etat].taxationBank(ite.McountryBank,ite.McountryCentralBank)

            for country in ite.McountryBank:
                for bank in ite.McountryBank[country]:
                    ite.McountryBank[country][bank].distributingDividends(ite.McountryConsumer,ite.McountryBank,ite.McountryCentralBank)

            enEx.exitBank(ite.McountryConsumer,ite.McountryFirm,ite.McountryBank,ite.McountryCentralBank,ite.McountryEtat)

            enEx.enter(ite.McountryConsumer,ite.McountryFirm,t,ite.McountryBank,ite.McountryCentralBank,aggrega.McountryAvPrice,ite.McountryEtat) 

            for country in ite.McountryConsumer:
                for consumer in ite.McountryConsumer[country]:
                    ite.McountryConsumer[country][consumer].ownershipCheck(ite.McountryBank)

            maDeposit.creatingAccount(ite.McountryConsumer,ite.McountryFirm,ite.McountryBank,ite.McountryCentralBank)

            maDeposit.allocatingConsumerDeposit(ite.McountryConsumer,ite.McountryBank)

            for country in ite.McountryCentralBank:
                ite.McountryCentralBank[country].balancing(ite.McountryConsumer,ite.McountryFirm,ite.McountryEtat,centralBankUnion,aggrega.DTBC) 

            aggrega.checkCA(ite.McountryConsumer,t,run,ite.McountryFirm,ite.McountryEtat,ite.McountryBank,ite.McountryCentralBank,
                     maCredit.creditCapitalInflow,maCredit.creditCapitalOutflow,
                     maBonds.creditBondInflow,maBonds.creditBondOutflow,enEx.DcountryFirmGone,enEx.DcountryBankGone,\
                     enEx.DcountryForeignBankLosses,t)

            aggrega.checkNetWorth(ite.McountryConsumer,ite.McountryFirm,ite.McountryBank,ite.McountryCentralBank,ite.McountryEtat,\
                                       enEx.DpastBondExit) 

            centralBankUnion.taylorRule1(aggrega.McountryInflation,aggrega.McountryUnemployement,\
                                        ite.McountryBank,ite.McountryCentralBank,t,ite.McountryConsumer,ite.McountryFirm)

            ite.debtExplotionBreak(aggrega.McountryY,t)

            if ite.breaking=='yes':
                  break 


    metrics_summary = aggrega.core_metrics_summary()
    metrics_series = aggrega.metric_series()
    result = {
        'core_metrics': metrics_summary,
        'metric_series': metrics_series,
    }

    if progress:
        print        
        print 'the end'       

    return result


DEFAULT_HORIZONS = {
    'ab': 240,
    'scenario': 250,
    'robustness': 120,
}


def run_ab_demo(run_id=0, ncycle=None, output_root=None, parameter_overrides=None, llm_overrides=None, progress=False, mode='ab'):
    """Run OFF and ON back-to-back with a shared seed and return output metadata.

    Args:
        run_id (int): Seed identifier mirrored into ``Parameter.Lrun``.
        ncycle (int): Horizon for the short demo runs (defaults to 240).
        output_root (str): Directory where OFF/ON subfolders are created.
        parameter_overrides (dict): Optional ``Parameter`` attribute overrides applied
            to both OFF and ON configurations (example: ``{"ncycle": 120}``).
        llm_overrides (dict): Attribute overrides applied only when the ON run executes
            (example: ``{"use_llm_firm_pricing": True}``).
        progress (bool): When ``True`` preserve the legacy "the end" footer printouts.

    Returns:
        dict: ``{"off": {...}, "on": {...}}`` metadata with output folders and run settings.
    """

    parameter_overrides = parameter_overrides or {}
    llm_overrides = llm_overrides or {}
    base_dir = output_root or os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'artifacts', 'ab_demo'))
    results = {}
    default_horizon = DEFAULT_HORIZONS.get(mode, DEFAULT_HORIZONS['ab'])

    for label, llm_enabled in (('off', False), ('on', True)):
        para = Parameter()
        para.Lrun = [run_id]
        para.weSeedRun='yes'
        effective_cycles = ncycle if ncycle is not None else default_horizon
        para.ncycle = parameter_overrides.get('ncycle', effective_cycles)
        para.LtimeCollecting = list(range(para.ncycle))
        run_root = os.path.join(base_dir, 'run_%03d' % run_id, label)
        para.folder = os.path.abspath(run_root)

        for attr, value in parameter_overrides.items():
            if attr in ('folder', 'Lrun', 'use_llm_firm_pricing', 'use_llm_bank_credit', 'use_llm_wage'):
                continue
            setattr(para, attr, value)

        para.use_llm_firm_pricing = llm_enabled
        para.use_llm_bank_credit = llm_enabled
        para.use_llm_wage = llm_enabled

        for attr, value in llm_overrides.items():
            setattr(para, attr, value)

        sim_output = run_simulation(para, progress=progress)
        if isinstance(sim_output, dict):
            core_metrics = sim_output.get('core_metrics', {})
            metric_series = sim_output.get('metric_series', {})
        else:
            core_metrics = {}
            metric_series = {}

        results[label] = {
            'folder': para.folder,
            'run_id': run_id,
            'ncycle': para.ncycle,
            'mode': mode,
            'llm': {
                'firm_pricing': para.use_llm_firm_pricing,
                'bank_credit': para.use_llm_bank_credit,
                'wage': para.use_llm_wage,
            },
            'artifacts': _collect_artifacts(para.folder),
            'counters': _counters_summary(),
            'core_metrics': core_metrics,
            'metric_series': metric_series,
        }

    _write_core_metrics(results)

    return results


def _collect_artifacts(folder):
    csv_paths = sorted(glob.glob(os.path.join(folder, '*.csv')))
    png_paths = sorted(glob.glob(os.path.join(folder, '*.png')))
    return {
        'csv': csv_paths,
        'png': png_paths,
    }


def _counters_summary():
    timing_log = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'timing.log'))
    summary = {
        'timing_log': timing_log,
        'fallbacks': 0,
        'timeouts': 0,
    }
    return summary


def _write_core_metrics(results):
    """Persist core metrics for OFF/ON scenarios under data/core_metrics.csv."""

    rows = []
    scenario_map = {'off': 'baseline', 'on': 'llm_on'}
    for label, payload in results.items():
        scenario = scenario_map.get(label, label)
        metrics = payload.get('core_metrics') or {}
        for metric_name, value in metrics.items():
            rows.append((scenario, metric_name, value))

    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
    if not os.path.isdir(data_dir):
        os.makedirs(data_dir)

    file_path = os.path.join(data_dir, 'core_metrics.csv')
    with open(file_path, 'wb') as handle:
        writer = csv.writer(handle, lineterminator='\n')
        writer.writerow(['scenario', 'metric', 'value'])
        for scenario, metric_name, value in rows:
            writer.writerow([scenario, metric_name, value])


if __name__ == "__main__":
    run_simulation()
