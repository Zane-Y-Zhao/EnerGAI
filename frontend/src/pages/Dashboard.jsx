import React, { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import * as echarts from 'echarts'

const MAX_DATA_POINTS = 20

const Dashboard = () => {
  const navigate = useNavigate()
  const [kpiData, setKpiData] = useState(null)
  const [equipmentList, setEquipmentList] = useState([])
  const [alerts, setAlerts] = useState([])
  const [currentTime, setCurrentTime] = useState(new Date().toLocaleTimeString())

  const trendChartRef = useRef(null)
  const historyChartRef = useRef(null)
  const energyChartRef = useRef(null)
  const trendChartInstance = useRef(null)
  const historyChartInstance = useRef(null)
  const energyChartInstance = useRef(null)
  const trendBufferRef = useRef({
    labels: [],
    temperature: [],
    pressure: [],
    heatRecovery: []
  })

  useEffect(() => {
    loadInitialData()
    const timeInterval = setInterval(() => {
      setCurrentTime(new Date().toLocaleTimeString())
    }, 1000)

    return () => {
      clearInterval(timeInterval)
    }
  }, [])

  useEffect(() => {
    if (trendChartRef.current && !trendChartInstance.current) {
      initTrendChart()
    }
    if (historyChartRef.current && !historyChartInstance.current) {
      initHistoryChart()
    }
  }, [])

  useEffect(() => {
    if (energyChartRef.current && !energyChartInstance.current) {
      initEnergyChart()
    }
  }, [])

  useEffect(() => {
    if (kpiData && trendChartInstance.current) {
      updateTrendData()
    }
  }, [kpiData])

  useEffect(() => {
    if (equipmentList.length > 0 && alerts.length > 0) {
      if (!energyChartInstance.current && energyChartRef.current) {
        initEnergyChart()
      }
    }
  }, [equipmentList, alerts])

  const loadInitialData = async () => {
    try {
      const [kpiRes, equipmentRes, alertsRes] = await Promise.all([
        fetch('/api/v1/kpi').then(r => r.json()),
        fetch('/api/v1/equipment').then(r => r.json()),
        fetch('/api/v1/alerts').then(r => r.json())
      ])
      setKpiData(kpiRes)
      setEquipmentList(equipmentRes)
      setAlerts(alertsRes)
    } catch (error) {
      console.error('加载数据失败:', error)
    }
  }

  const initTrendChart = () => {
    if (!trendChartRef.current) return

    trendChartInstance.current = echarts.init(trendChartRef.current)

    const initialOption = {
      backgroundColor: 'transparent',
      animation: true,
      animationDuration: 300,
      animationEasing: 'linear',
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(30, 30, 50, 0.9)',
        borderColor: 'rgba(255, 255, 255, 0.2)',
        borderWidth: 1,
        textStyle: { color: '#fff' }
      },
      legend: {
        data: ['温度', '压力', '回收热量'],
        textStyle: { color: 'rgba(255, 255, 255, 0.7)' },
        top: 0,
        right: 0
      },
      grid: { left: '3%', right: '4%', bottom: '3%', top: '15%', containLabel: true },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: [],
        axisLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.2)' } },
        axisLabel: { color: 'rgba(255, 255, 255, 0.6)', fontSize: 11 }
      },
      yAxis: {
        type: 'value',
        axisLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.2)' } },
        axisLabel: { color: 'rgba(255, 255, 255, 0.6)', fontSize: 11 },
        splitLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.1)' } }
      },
      series: [
        {
          name: '温度',
          type: 'line',
          data: [],
          smooth: true,
          symbol: 'none',
          lineStyle: { color: '#38bdf8', width: 2 },
          itemStyle: { color: '#38bdf8' },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(56, 189, 248, 0.4)' },
              { offset: 1, color: 'rgba(56, 189, 248, 0.05)' }
            ])
          }
        },
        {
          name: '压力',
          type: 'line',
          data: [],
          smooth: true,
          symbol: 'none',
          lineStyle: { color: '#22d3ee', width: 2 },
          itemStyle: { color: '#22d3ee' },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(34, 211, 238, 0.4)' },
              { offset: 1, color: 'rgba(34, 211, 238, 0.05)' }
            ])
          }
        },
        {
          name: '回收热量',
          type: 'line',
          data: [],
          smooth: true,
          symbol: 'none',
          lineStyle: { color: '#818cf8', width: 2 },
          itemStyle: { color: '#818cf8' },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(129, 140, 248, 0.4)' },
              { offset: 1, color: 'rgba(129, 140, 248, 0.05)' }
            ])
          }
        }
      ]
    }

    trendChartInstance.current.setOption(initialOption)

    window.addEventListener('resize', () => {
      if (trendChartInstance.current) {
        trendChartInstance.current.resize()
      }
    })

    const dataInterval = setInterval(async () => {
      try {
        const kpiRes = await fetch('/api/v1/kpi').then(r => r.json())
        setKpiData(kpiRes)
      } catch (error) {
        console.error('更新数据失败:', error)
      }
    }, 3000)

    return () => clearInterval(dataInterval)
  }

  const initHistoryChart = () => {
    if (!historyChartRef.current) return

    historyChartInstance.current = echarts.init(historyChartRef.current)

    const generate24hData = () => {
      const labels = []
      const temperature = []
      const pressure = []
      const heatRecovery = []

      for (let i = 24; i >= 0; i--) {
        const hour = (Math.floor(Date.now() / 3600000) - i) % 24
        labels.push(`${hour.toString().padStart(2, '0')}:00`)
        temperature.push(75 + Math.random() * 15 + Math.sin(i / 3) * 5)
        pressure.push(3.8 + Math.random() * 0.8 + Math.cos(i / 4) * 0.3)
        heatRecovery.push(1000 + Math.random() * 300 + Math.sin(i / 2) * 100)
      }

      return { labels, temperature, pressure, heatRecovery }
    }

    const data = generate24hData()

    const option = {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(30, 30, 50, 0.9)',
        borderColor: 'rgba(255, 255, 255, 0.2)',
        borderWidth: 1,
        textStyle: { color: '#fff' }
      },
      legend: {
        data: ['温度', '压力', '回收热量'],
        textStyle: { color: 'rgba(255, 255, 255, 0.7)' },
        top: 0,
        right: 0
      },
      grid: { left: '3%', right: '4%', bottom: '3%', top: '15%', containLabel: true },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: data.labels,
        axisLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.2)' } },
        axisLabel: { color: 'rgba(255, 255, 255, 0.6)', fontSize: 11, interval: 3 }
      },
      yAxis: {
        type: 'value',
        axisLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.2)' } },
        axisLabel: { color: 'rgba(255, 255, 255, 0.6)', fontSize: 11 },
        splitLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.1)' } }
      },
      series: [
        {
          name: '温度',
          type: 'line',
          data: data.temperature,
          smooth: true,
          symbol: 'circle',
          symbolSize: 4,
          lineStyle: { color: '#38bdf8', width: 2 },
          itemStyle: { color: '#38bdf8' }
        },
        {
          name: '压力',
          type: 'line',
          data: data.pressure,
          smooth: true,
          symbol: 'circle',
          symbolSize: 4,
          lineStyle: { color: '#22d3ee', width: 2 },
          itemStyle: { color: '#22d3ee' }
        },
        {
          name: '回收热量',
          type: 'line',
          data: data.heatRecovery,
          smooth: true,
          symbol: 'circle',
          symbolSize: 4,
          lineStyle: { color: '#818cf8', width: 2 },
          itemStyle: { color: '#818cf8' }
        }
      ]
    }

    historyChartInstance.current.setOption(option)

    window.addEventListener('resize', () => {
      if (historyChartInstance.current) {
        historyChartInstance.current.resize()
      }
    })
  }

  const updateTrendData = () => {
    if (!trendChartInstance.current || !kpiData) return

    const now = new Date()
    const timeLabel = now.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    const buffer = trendBufferRef.current

    buffer.labels.push(timeLabel)
    buffer.temperature.push(kpiData.temperature)
    buffer.pressure.push(kpiData.pressure)
    buffer.heatRecovery.push(kpiData.heatRecovery)

    if (buffer.labels.length > MAX_DATA_POINTS) {
      buffer.labels.shift()
      buffer.temperature.shift()
      buffer.pressure.shift()
      buffer.heatRecovery.shift()
    }

    trendChartInstance.current.setOption({
      xAxis: { data: buffer.labels },
      series: [
        { data: buffer.temperature },
        { data: buffer.pressure },
        { data: buffer.heatRecovery }
      ]
    }, false)
  }

  const initEnergyChart = () => {
    if (!energyChartRef.current) return

    energyChartInstance.current = echarts.init(energyChartRef.current)

    const data = {
      labels: ['反应釜', '换热器', '泵', '冷却系统'],
      actual: [120, 80, 45, 60],
      target: [100, 70, 40, 50]
    }

    const option = {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(30, 30, 50, 0.9)',
        borderColor: 'rgba(255, 255, 255, 0.2)',
        borderWidth: 1,
        textStyle: { color: '#fff' },
        axisPointer: { type: 'shadow' }
      },
      legend: {
        data: ['实际能耗', '节能目标'],
        textStyle: { color: 'rgba(255, 255, 255, 0.7)' },
        top: 0,
        right: 0
      },
      grid: { left: '3%', right: '4%', bottom: '3%', top: '15%', containLabel: true },
      xAxis: {
        type: 'category',
        data: data.labels,
        axisLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.2)' } },
        axisLabel: { color: 'rgba(255, 255, 255, 0.6)', fontSize: 11 }
      },
      yAxis: {
        type: 'value',
        axisLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.2)' } },
        axisLabel: { color: 'rgba(255, 255, 255, 0.6)', fontSize: 11 },
        splitLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.1)' } }
      },
      series: [
        {
          name: '实际能耗',
          type: 'bar',
          data: data.actual,
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#38bdf8' },
              { offset: 1, color: '#2563eb' }
            ])
          },
          barWidth: '30%',
          borderRadius: [4, 4, 0, 0]
        },
        {
          name: '节能目标',
          type: 'bar',
          data: data.target,
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#67e8f9' },
              { offset: 1, color: '#6366f1' }
            ])
          },
          barWidth: '30%',
          borderRadius: [4, 4, 0, 0]
        }
      ]
    }

    energyChartInstance.current.setOption(option)

    window.addEventListener('resize', () => {
      if (energyChartInstance.current) {
        energyChartInstance.current.resize()
      }
    })
  }

  const exportChart = (chartType) => {
    let chart
    let filename

    if (chartType === 'trend') {
      chart = trendChartInstance.current
      filename = '实时趋势图'
    } else if (chartType === 'history') {
      chart = historyChartInstance.current
      filename = '24h历史趋势图'
    } else if (chartType === 'energy') {
      chart = energyChartInstance.current
      filename = '能耗分析图'
    }

    if (chart) {
      const dataURL = chart.getDataURL({
        pixelRatio: 2,
        backgroundColor: '#020617'
      })

      const link = document.createElement('a')
      link.download = `${filename}_${new Date().toISOString().slice(0, 10)}.png`
      link.href = dataURL
      link.click()
    }
  }

  const exportToCSV = () => {
    let csvContent = "数据类型,当前值,预测值\n"

    if (kpiData) {
      csvContent += `余热温度,${kpiData.temperature},${kpiData.temperaturePrediction}\n`
      csvContent += `系统压力,${kpiData.pressure},${kpiData.pressurePrediction}\n`
      csvContent += `余热回收,${kpiData.heatRecovery},${kpiData.heatRecoveryPrediction}\n`
      csvContent += `节能效果,${kpiData.energySaving},${kpiData.energySavingPrediction}\n`
    }

    const buffer = trendBufferRef.current
    if (buffer.labels.length > 0) {
      csvContent += "\n时间,温度,压力,回收热量\n"
      for (let i = 0; i < buffer.labels.length; i++) {
        csvContent += `${buffer.labels[i]},${buffer.temperature[i]},${buffer.pressure[i]},${buffer.heatRecovery[i]}\n`
      }
    }

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    link.setAttribute('download', `EnerGAI数据_${new Date().toISOString().slice(0, 10)}.csv`)
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const getStatusText = (status) => {
    if (status === 'warning') return '维护'
    if (status === 'error') return '故障'
    return '正常'
  }

  return (
    <div className="dashboard">
      <div className="ambient-bg" aria-hidden="true">
        <div className="ambient-bg__base"></div>
        <div className="ambient-bg__aurora"></div>
        <div className="ambient-bg__aurora ambient-bg__aurora--slow"></div>
        <div className="ambient-bg__mesh"></div>
        <div className="ambient-bg__hex"></div>
        <div className="ambient-bg__flow"></div>
        <div className="ambient-bg__flow ambient-bg__flow--vert"></div>
        <div className="ambient-bg__sweep"></div>
        <div className="ambient-bg__rings"><span></span><span></span><span></span></div>
        <div className="ambient-bg__glow ambient-bg__glow--a"></div>
        <div className="ambient-bg__glow ambient-bg__glow--b"></div>
        <div className="ambient-bg__glow ambient-bg__glow--c"></div>
        <div className="ambient-bg__glow ambient-bg__glow--d"></div>
        <div className="ambient-bg__sparkles"></div>
        <div className="ambient-bg__vignette"></div>
      </div>

      <div className="header">
        <div className="header-left">
          <h1>EnerGAI</h1>
          <button className="action-btn execute" onClick={exportToCSV}>导出CSV</button>
        </div>
        <div className="status">
          <div className="status-item">
            <div className="status-indicator online"></div>
            <span>系统运行正常</span>
          </div>
          <div className="status-item">
            <span>实时监控中</span>
          </div>
          <div className="status-item">
            <span id="currentTime">{currentTime}</span>
          </div>
        </div>
      </div>

      <div className="grid">
        <div className="left-panel">
          <div className="card">
            <h2>综合概览</h2>
            <div className="kpi-grid" id="kpiGrid">
              {kpiData && (
                <>
                  <div className="kpi-card">
                    <div className="kpi-label">余热温度</div>
                    <div className="kpi-value">{kpiData.temperature}<span className="kpi-unit">°C</span></div>
                    <div className="kpi-prediction">预测: {kpiData.temperaturePrediction}°C</div>
                  </div>
                  <div className="kpi-card">
                    <div className="kpi-label">系统压力</div>
                    <div className="kpi-value">{kpiData.pressure}<span className="kpi-unit">MPa</span></div>
                    <div className="kpi-prediction">预测: {kpiData.pressurePrediction}MPa</div>
                  </div>
                  <div className="kpi-card">
                    <div className="kpi-label">余热回收</div>
                    <div className="kpi-value">{kpiData.heatRecovery}<span className="kpi-unit">kJ</span></div>
                    <div className="kpi-prediction">预测: {kpiData.heatRecoveryPrediction}kJ</div>
                  </div>
                  <div className="kpi-card">
                    <div className="kpi-label">节能效果</div>
                    <div className="kpi-value">{kpiData.energySaving}<span className="kpi-unit">kW</span></div>
                    <div className="kpi-prediction">预测: {kpiData.energySavingPrediction}kW</div>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>

        <div className="center-top-panel">
          <div className="card trend-card">
            <div className="card-header">
              <h2>实时趋势</h2>
              <div className="card-actions">
                <button className="action-btn view" onClick={() => exportChart('trend')}>导出</button>
              </div>
            </div>
            <div className="chart-container" ref={trendChartRef}></div>
          </div>
          <div className="card trend-card">
            <div className="card-header">
              <h2>过去24小时</h2>
              <div className="card-actions">
                <button className="action-btn view" onClick={() => exportChart('history')}>导出</button>
              </div>
            </div>
            <div className="chart-container" ref={historyChartRef}></div>
          </div>
        </div>

        <div className="right-panel">
          <div className="right-top">
            <div className="card">
              <h2>预警信息</h2>
              <div className="alert-list">
                {alerts.length === 0 ? (
                  <div className="alert-item info">
                    <div className="alert-message">暂无预警信息</div>
                  </div>
                ) : (
                  alerts.map((alert, index) => (
                    <div key={index} className={`alert-item ${alert.level}`}>
                      <div className="alert-message">{alert.message}</div>
                      <div className="alert-time">{alert.time}</div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>

          <div className="right-middle">
            <div className="card">
              <h2>智能操作建议</h2>
              <div className="recommendation-list">
                <div className="recommendation-item">
                  <div className="recommendation-content">基于当前余热温度85.5°C和压力4.2MPa的分析，建议调整换热器1的运行参数</div>
                  <div className="recommendation-actions">
                    <button className="action-btn execute">立即执行</button>
                    <button className="action-btn view">查看依据</button>
                    <button className="action-btn ignore">忽略</button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="right-bottom">
            <div className="card ai-assistant-btn-card">
              <button
                className="ai-assistant-big-btn"
                onClick={() => navigate('/ai-assistant')}
              >
                <span className="ai-icon">🤖</span>
                <span className="ai-text">AI智能助手</span>
              </button>
            </div>
          </div>
        </div>

        <div className="center-bottom-left">
          <div className="card">
            <div className="card-header">
              <h2>能耗分析</h2>
              <div className="card-actions">
                <button className="action-btn view" onClick={() => exportChart('energy')}>导出图表</button>
              </div>
            </div>
            <div className="energy-chart" ref={energyChartRef}></div>
          </div>
        </div>

        <div className="center-bottom-right">
          <div className="card">
            <h2>设备状态</h2>
            <div className="equipment-grid">
              {equipmentList.map((equipment, index) => (
                <div key={index} className={`equipment-card ${equipment.status}`}>
                  <div className="equipment-name">{equipment.name}</div>
                  <div className={`equipment-status ${equipment.status}`}>{getStatusText(equipment.status)}</div>
                  {equipment.health && <div className="equipment-health">健康度: {equipment.health}%</div>}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Dashboard